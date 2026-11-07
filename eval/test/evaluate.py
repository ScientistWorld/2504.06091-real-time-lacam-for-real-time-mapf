"""Held-out evaluator for bounded real-time MAPF planners.

Self-contained by design: it shares no code with eval/train, never imports
method/ or baseline/, and never reads files a method writes except the planner
manifests under ``outputs/planners/``.

For every registered planner and every experiment it

1. builds the held-out instances itself (embedded map, generators and seeds
   live only in this file);
2. runs the planner online in a fresh worker process: at every tick the
   planner receives the current joint configuration and returns the next one;
3. meters the planner's planning work itself (executed Python line events),
   charges work beyond the per-tick budget as extra ticks during which every
   agent waits, rejects illegal moves, and stops at the tick horizon;
4. scores the path it recorded. Nothing the planner reports is trusted.

The comparison rows (full-horizon LaCAM and naive restart real-time LaCAM)
are frozen copies owned by this evaluator and run under the same meter.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import random
import secrets
import subprocess
import sys
import threading
import types
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SLICE = "test"
_THIS_FILE = globals().get("__file__")
# Workers run this evaluator's source text in memory (python -c), so they find
# the workspace through the environment the parent sets.
WORKSPACE = Path(_THIS_FILE).resolve().parents[2] if _THIS_FILE else Path(os.environ["RTMAPF_WORKSPACE"])
WORKER_OK = 17  # exit status of a worker that finished its own bookkeeping
BASELINES = ("full_lacam", "naive_rt_lacam")
WORKER_WALL_TIMEOUT = 1800  # safety net only; scoring never uses wall-clock time
IMPORT_WORK_CAP = 200_000  # metered events allowed for importing a planner module

# ----------------------------------------------------------------------------
# Operating points (fixed by the evaluator)
# ----------------------------------------------------------------------------
# budget        planning work allowed per tick (metered line events). Work
#               beyond it delays the decision by whole ticks (agents wait).
# work_cap      cumulative planning work allowed per episode (the analogue of
#               the paper's cumulative planning timeout).
# horizon       execution ticks allowed per episode: HORIZON_FACTOR times the
#               ticks needed to spend work_cap at the full per-tick budget.
HORIZON_FACTOR = 2
SCALED_BUDGET = 1000
SCALED_WORK_CAP = 2_000_000
MOVINGAI_BUDGET = 3000
MOVINGAI_WORK_CAP = 6_000_000

EXPERIMENTS = {
    "scaled_small_mapf": {"family": "scaled", "budget": SCALED_BUDGET, "work_cap": SCALED_WORK_CAP},
    "scaled_small_mapf_budget3": {"family": "scaled", "budget": 3 * SCALED_BUDGET, "work_cap": SCALED_WORK_CAP},
    "movingai_random32": {"family": "movingai", "budget": MOVINGAI_BUDGET, "work_cap": MOVINGAI_WORK_CAP},
}

# Held-out instance seeds (train uses different seeds).
SCALED_SEED = 0x7E57_51A1_C0DE_0001
MOVINGAI_SEED = 0x7E57_51A1_C0DE_0002
SCALED_LAYOUT = (("corridor", 10), ("cross", 8), ("dense", 22))
MOVINGAI_AGENTS = tuple(n for n in (6, 8, 10, 12) for _ in range(8))
# Train and test are disjoint by construction: a candidate instance belongs to
# the slice whose parity matches a hash of its agent-order-invariant form.
SLICE_PARITY = 1

# MovingAI MAPF benchmark map random-32-32-20 (Stern et al. 2019), embedded so
# that edits to downloaded files cannot change the evaluated tasks.
RANDOM_32_32_20 = (
    "..........@......@...@.@........",
    "@...@.@@...........@.@...@......",
    "..............@........@@...@...",
    ".....@.@..........@..........@..",
    ".@@...........@@.@......@..@....",
    "......@..@.@..@@......@....@..@@",
    "......@..@@........@.......@...@",
    ".@...@...............@@...@..@..",
    "......@.........@.......@.@.....",
    "..@.@............@.@.......@@...",
    "@.@.........@.@.......@...@.....",
    "............@.....@.@.@.......@.",
    "..@.....@.@.@@.@..........@.....",
    ".@................@.@.....@...@.",
    "...@@@.......@.........@........",
    "........@....@.@.@..@...........",
    "..@...@........@....@..@@@....@.",
    ".@......@@@..@.@..@.@..@@....@T@",
    "@.........@........@..@......@@@",
    "......@...@..@..@.@...@...@.....",
    ".@.@........@.........@@.@...@..",
    ".......@.@........@..@@@..@@@...",
    "..@.@..@....@......@..........@.",
    ".......@.....@....@...@.@.@@....",
    ".................@...@.@..@.@...",
    "................@........@..@..@",
    ".@......@.@.........@@.........@",
    "..@..@..@.......................",
    "@..@@......@...@...@.........@@@",
    "@....@....@....@.@.@...@......@@",
    "@@.@..@@.@.@@.....@........@....",
    "@@.............@..@.........@...",
)


# ----------------------------------------------------------------------------
# Instances
# ----------------------------------------------------------------------------
class Instance:
    def __init__(self, name, width, height, obstacles, starts, goals):
        self.name = name
        self.width = int(width)
        self.height = int(height)
        self.obstacles = frozenset((int(x), int(y)) for x, y in obstacles)
        self.starts = tuple((int(x), int(y)) for x, y in starts)
        self.goals = tuple((int(x), int(y)) for x, y in goals)
        self.n_agents = len(self.starts)
        self.nbrs = {}
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.obstacles:
                    continue
                out = [(x, y)]
                for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                    nb = (x + dx, y + dy)
                    if 0 <= nb[0] < self.width and 0 <= nb[1] < self.height and nb not in self.obstacles:
                        out.append(nb)
                self.nbrs[(x, y)] = tuple(out)
        self.dist = tuple(_bfs(self.nbrs, g) for g in self.goals)
        self.lower_bound = sum(self.dist[i][s] for i, s in enumerate(self.starts))

    def to_json(self):
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "obstacles": sorted(self.obstacles),
            "starts": list(self.starts),
            "goals": list(self.goals),
        }

    @staticmethod
    def from_json(obj):
        return Instance(obj["name"], obj["width"], obj["height"], obj["obstacles"], obj["starts"], obj["goals"])

    def planner_view(self):
        """Fresh copies handed to a planner; the evaluator keeps its own."""
        return {
            "width": self.width,
            "height": self.height,
            "obstacles": frozenset(self.obstacles),
            "starts": tuple(self.starts),
            "goals": tuple(self.goals),
            "neighbors": dict(self.nbrs),
            "dist": tuple(dict(d) for d in self.dist),
        }


def _bfs(nbrs, source):
    dist = {source: 0}
    queue = deque([source])
    while queue:
        cell = queue.popleft()
        d = dist[cell] + 1
        for nb in nbrs[cell]:
            if nb not in dist:
                dist[nb] = d
                queue.append(nb)
    return dist


def _largest_component(width, height, obstacles):
    free = {(x, y) for y in range(height) for x in range(width) if (x, y) not in obstacles}
    best = set()
    seen = set()
    for cell in sorted(free):
        if cell in seen:
            continue
        comp = {cell}
        queue = deque([cell])
        while queue:
            x, y = queue.popleft()
            for nb in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
                if nb in free and nb not in comp:
                    comp.add(nb)
                    queue.append(nb)
        seen |= comp
        if len(comp) > len(best):
            best = comp
    return best


def _sample_agents(rng, cells, n):
    cells = sorted(cells)
    while True:
        starts = rng.sample(cells, n)
        goals = rng.sample(cells, n)
        if all(s != g for s, g in zip(starts, goals)):
            return starts, goals


def _corridor(rng, name):
    length = rng.randint(8, 11)
    n_left, n_right = rng.choice(((1, 1), (1, 2), (2, 1)))
    n_pockets = rng.randint(min(n_left, n_right), min(n_left, n_right) + 1)
    free = {(x, 1) for x in range(length)}
    for px in rng.sample(range(2, length - 2), n_pockets):
        free.add((px, rng.choice((0, 2))))
    obstacles = {(x, y) for y in range(3) for x in range(length)} - free
    starts = [(j, 1) for j in range(n_left)] + [(length - 1 - j, 1) for j in range(n_right)]
    goals = [(length - n_left + j, 1) for j in range(n_left)] + [(n_right - 1 - j, 1) for j in range(n_right)]
    return Instance(name, length, 3, obstacles, starts, goals)


def _cross(rng, name):
    left, right, up, down = (rng.randint(3, 4) for _ in range(4))
    width, height = left + right + 1, up + down + 1
    cx, cy = left, up
    free = {(x, cy) for x in range(width)} | {(cx, y) for y in range(height)}
    alcoves = [(cx - 1, cy - 1), (cx + 1, cy - 1), (cx - 1, cy + 1), (cx + 1, cy + 1)]
    free |= set(rng.sample(alcoves, rng.choice((3, 4))))
    obstacles = {(x, y) for y in range(height) for x in range(width)} - free
    ends = [((0, cy), (width - 1, cy)), ((width - 1, cy), (0, cy)), ((cx, 0), (cx, height - 1)), ((cx, height - 1), (cx, 0))]
    starts = [s for s, _ in ends]
    goals = [g for _, g in ends]
    order = list(range(len(starts)))
    rng.shuffle(order)
    return Instance(name, width, height, obstacles, [starts[i] for i in order], [goals[i] for i in order])


def _dense(rng, name):
    while True:
        size = rng.choice((8, 9))
        density = rng.uniform(0.12, 0.2)
        n = rng.randint(5, 7)
        obstacles = {(x, y) for y in range(size) for x in range(size) if rng.random() < density}
        comp = _largest_component(size, size, obstacles)
        if len(comp) < 2 * n + 8:
            continue
        obstacles |= {(x, y) for y in range(size) for x in range(size)} - comp
        starts, goals = _sample_agents(rng, comp, n)
        return Instance(name, size, size, obstacles, starts, goals)


def _canonical(inst):
    return repr((inst.width, inst.height, sorted(inst.obstacles), sorted(zip(inst.starts, inst.goals))))


def _accept(inst, seen):
    """Reject duplicates (up to agent relabelling) and the other slice's instances."""
    key = _canonical(inst)
    if key in seen or hashlib.sha256(key.encode()).digest()[0] % 2 != SLICE_PARITY:
        return False
    seen.add(key)
    return True


def scaled_instances():
    rng = random.Random(SCALED_SEED)
    out = []
    seen = set()
    makers = {"corridor": _corridor, "cross": _cross, "dense": _dense}
    for kind, count in SCALED_LAYOUT:
        k = 0
        tries = 0
        while k < count:
            tries += 1
            if tries > 100_000:
                raise RuntimeError(f"cannot draw {count} distinct {kind} instances")
            inst = makers[kind](rng, f"{SLICE}_{kind}_{k}")
            if _accept(inst, seen):
                out.append(inst)
                k += 1
    return out


def movingai_instances():
    assert len(RANDOM_32_32_20) == 32 and all(len(row) == 32 for row in RANDOM_32_32_20)
    width, height = len(RANDOM_32_32_20[0]), len(RANDOM_32_32_20)
    obstacles = {(x, y) for y, row in enumerate(RANDOM_32_32_20) for x, ch in enumerate(row) if ch in "@T"}
    comp = _largest_component(width, height, obstacles)
    obstacles |= {(x, y) for y in range(height) for x in range(width)} - comp
    rng = random.Random(MOVINGAI_SEED)
    out = []
    seen = set()
    for k, n in enumerate(MOVINGAI_AGENTS):
        while True:
            starts, goals = _sample_agents(rng, comp, n)
            inst = Instance(f"{SLICE}_random32_{n}a_{k}", width, height, obstacles, starts, goals)
            if _accept(inst, seen):
                out.append(inst)
                break
    return out


def horizon_for(budget, work_cap):
    return HORIZON_FACTOR * work_cap // budget


def instances_for(family):
    return scaled_instances() if family == "scaled" else movingai_instances()


# ----------------------------------------------------------------------------
# Path checks and cost
# ----------------------------------------------------------------------------
def legal_move(inst, prev, nxt):
    if len(nxt) != inst.n_agents or len(set(nxt)) != len(nxt):
        return False
    nbrs = inst.nbrs
    for a, b in zip(prev, nxt):
        if a not in nbrs or b not in nbrs[a]:
            return False
    where = {cell: i for i, cell in enumerate(prev)}
    for j, b in enumerate(nxt):
        if b != prev[j]:
            i = where.get(b)
            if i is not None and nxt[i] == prev[j]:
                return False
    return True


def legal_path(inst, path):
    if not path or path[0] != inst.starts:
        return False
    return all(legal_move(inst, a, b) for a, b in zip(path, path[1:]))


def path_cost(inst, path):
    """Sum of costs: unit cost per agent per tick, except staying at its goal."""
    goals = inst.goals
    cost = 0
    for prev, cur in zip(path, path[1:]):
        for i, (a, b) in enumerate(zip(prev, cur)):
            if a != goals[i] or b != goals[i]:
                cost += 1
    return cost


def _parse_config(obj, n_agents):
    """Accept only built-in list/tuple of int pairs (no user code can run)."""
    if type(obj) not in (list, tuple) or len(obj) != n_agents:
        return None
    out = []
    for cell in obj:
        if type(cell) not in (list, tuple) or len(cell) != 2:
            return None
        x, y = cell
        if type(x) is not int or type(y) is not int:
            return None
        out.append((x, y))
    return tuple(out)


# ----------------------------------------------------------------------------
# Work meter (runs inside the worker process)
# ----------------------------------------------------------------------------
class _BudgetAbort(BaseException):
    """Raised inside the planner when it exhausts the episode's planning work."""


class Meter:
    """Counts executed Python line and call events while the planner runs."""

    def __init__(self):
        state = [0, 0]  # [events so far, hard cap]
        self._state = state

        def local(frame, event, arg):
            if event == "line":
                state[0] += 1
                if state[0] > state[1]:
                    raise _BudgetAbort()
            return local

        def glob(frame, event, arg):
            state[0] += 1
            if state[0] > state[1]:
                raise _BudgetAbort()
            return local

        self._tracer = glob

    @property
    def count(self):
        return self._state[0]

    def set_cap(self, cap):
        self._state[1] = cap

    def call(self, fn, *args):
        """Run planner code under the meter. Returns (value, status)."""
        threads_before = threading.active_count()
        threading.settrace(self._tracer)
        sys.settrace(self._tracer)
        try:
            value = fn(*args)
        except _BudgetAbort:
            sys.settrace(None)
            threading.settrace(None)
            return None, "work_exhausted"
        except BaseException as exc:  # noqa: BLE001 - any planner failure fails the episode
            sys.settrace(None)
            threading.settrace(None)
            return None, f"planner_error:{type(exc).__name__}"
        intact = sys.gettrace() is self._tracer
        sys.settrace(None)
        threading.settrace(None)
        if self._state[0] > self._state[1]:
            return None, "work_exhausted"
        if not intact or threading.active_count() != threads_before:
            return None, "meter_violation"
        return value, None

    def clock(self, tick_end, budget):
        state = self._state

        def remaining():
            return tick_end - state[0]

        return types.SimpleNamespace(remaining=remaining, budget=budget)


def run_realtime(factory, inst, budget, work_cap):
    """Online episode: the evaluator executes every decision and keeps the path."""
    horizon = horizon_for(budget, work_cap)
    meter = Meter()
    path = [inst.starts]
    config = inst.starts
    ticks = 0
    tick_start = 0
    meter.set_cap(min(work_cap, horizon * budget))
    planner, status = meter.call(factory, inst.planner_view())
    while status is None:
        if config == inst.goals:
            status = "success"
            break
        if ticks >= horizon:
            status = "horizon"
            break
        # A decision may not run past the cumulative work cap or the horizon.
        meter.set_cap(min(work_cap, tick_start + (horizon - ticks) * budget))
        decision, status = meter.call(planner.step, config, meter.clock(tick_start + budget, budget))
        if status is not None:
            break
        used = meter.count - tick_start
        n_ticks = max(1, -(-used // budget))
        nxt = _parse_config(decision, inst.n_agents)
        if nxt is None or not legal_move(inst, config, nxt):
            status = "illegal_move"
            break
        for _ in range(n_ticks - 1):  # late decision: everybody waits
            path.append(config)
        path.append(nxt)
        ticks += n_ticks
        config = nxt
        tick_start = meter.count
    return {"status": status, "path": [list(map(list, c)) for c in path], "work": meter.count, "ticks": ticks}


def run_offline(inst, work_cap):
    """Full-horizon comparator: plans once, then executes the whole plan."""
    meter = Meter()
    meter.set_cap(work_cap)
    plan, status = meter.call(_frozen_full_horizon, inst.planner_view())
    if status is None:
        status = "success" if plan else "no_solution"
    return {"status": status, "path": [list(map(list, c)) for c in (plan or [])], "work": meter.count,
            "ticks": max(0, len(plan or []) - 1)}


# ----------------------------------------------------------------------------
# Frozen comparators (evaluator-owned copies; edits elsewhere cannot change them)
# ----------------------------------------------------------------------------
class _Node:
    __slots__ = ("config", "parent", "attempts", "generated")

    def __init__(self, config, parent=None):
        self.config = config
        self.parent = parent
        self.attempts = 0
        self.generated = set()


class _FrozenLaCAM:
    def __init__(self, instance, start=None):
        self.nbrs = instance["neighbors"]
        self.dist = instance["dist"]
        self.goals = tuple(instance["goals"])
        self.n_agents = len(self.goals)
        root = tuple(start if start is not None else instance["starts"])
        self.nodes = {root: _Node(root, None)}
        self.root = root
        self.cursor = root
        self.max_attempts = sum(5 ** k for k in range(1, self.n_agents + 1))
        self._attempt_cost = 0

    def _ordered_actions(self, agent, cell):
        dist = self.dist[agent]
        return sorted(self.nbrs[cell], key=lambda c: (dist.get(c, 10**6), c != cell, c))

    def _forced(self, config, attempt):
        if attempt == 0:
            return {}
        value = attempt - 1
        prefix = self.n_agents
        for p in range(1, self.n_agents + 1):
            if value < 5 ** p:
                prefix = p
                break
            value -= 5 ** p
        forced = {}
        for agent in range(prefix):
            digit = value % 5
            value //= 5
            actions = self._ordered_actions(agent, config[agent])
            forced[agent] = actions[digit % len(actions)]
        return forced

    def _generate(self, config, forced):
        nbrs = self.nbrs
        owner = {cell: i for i, cell in enumerate(config)}
        assigned = {}
        used = set()
        visiting = set()

        def edge_conflicts(agent, target):
            for other, other_target in assigned.items():
                if config[agent] == other_target and config[other] == target:
                    return True
            return False

        def assign(agent):
            if agent in assigned:
                return True
            if agent in visiting:
                return False
            visiting.add(agent)
            choices = [forced[agent]] if agent in forced else self._ordered_actions(agent, config[agent])
            for target in choices:
                if target not in nbrs[config[agent]] or target in used or edge_conflicts(agent, target):
                    continue
                displaced = owner.get(target)
                if displaced is not None and displaced != agent and displaced not in assigned:
                    if not assign(displaced):
                        continue
                    if target in used or edge_conflicts(agent, target):
                        continue
                assigned[agent] = target
                used.add(target)
                visiting.remove(agent)
                return True
            visiting.remove(agent)
            return False

        goals, dist = self.goals, self.dist
        order = sorted(range(self.n_agents), key=lambda i: (config[i] == goals[i], dist[i].get(config[i], 10**6), i))
        for agent in order:
            if not assign(agent):
                return None
        nxt = tuple(assigned[i] for i in range(self.n_agents))
        if len(set(nxt)) != len(nxt):
            return None
        for i in range(self.n_agents):
            for j in range(i + 1, self.n_agents):
                if config[i] == nxt[j] and config[j] == nxt[i]:
                    return None
        return nxt

    def attempt(self):
        node = self.nodes[self.cursor]
        if node.attempts > self.max_attempts:
            if node.parent is None:
                return "exhausted"
            self.cursor = node.parent
            return "backtrack"
        k = node.attempts
        node.attempts += 1
        succ = self._generate(node.config, self._forced(node.config, k))
        if succ is None or succ in node.generated:
            return "retry"
        node.generated.add(succ)
        if succ not in self.nodes:
            self.nodes[succ] = _Node(succ, node.config)
        self.cursor = succ
        return "advance"

    def advance(self, clock):
        first = True
        while self.cursor != self.goals:
            if not first and clock.remaining() < self._attempt_cost:
                break
            first = False
            before = clock.remaining()
            status = self.attempt()
            self._attempt_cost = max(before - clock.remaining(), (3 * self._attempt_cost) // 4)
            if status == "exhausted":
                break

    def path_to_root(self, config):
        path = [config]
        while self.nodes[config].parent is not None:
            config = self.nodes[config].parent
            path.append(config)
        path.reverse()
        return path


def _frozen_full_horizon(instance):
    solver = _FrozenLaCAM(instance)
    while solver.cursor != solver.goals:
        if solver.attempt() == "exhausted":
            return None
    return solver.path_to_root(solver.goals)


class _FrozenNaiveRestart:
    """Real-time LaCAM that rebuilds its search from scratch every tick."""

    def __init__(self, instance):
        self.instance = instance

    def step(self, config, clock):
        solver = _FrozenLaCAM(self.instance, start=config)
        solver.advance(clock)
        if solver.cursor == solver.root:
            return config
        return solver.path_to_root(solver.cursor)[1]


# ----------------------------------------------------------------------------
# Worker process: one episode, fresh interpreter
# ----------------------------------------------------------------------------
def _load_factory(entry, factory_name):
    path = Path(entry)
    if not path.is_absolute():
        path = WORKSPACE / path
    spec = importlib.util.spec_from_file_location(f"_planner_{abs(hash(str(path)))}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, factory_name)


def worker_main(argv):
    kind, entry, factory_name, result_path = argv
    sys.path.insert(0, str(WORKSPACE))
    os.chdir(WORKSPACE)
    factory = None
    load_error = None
    # The planner module is imported before the episode is read from stdin.
    if kind == "manifest":
        # Importing is metered too (not charged to any tick, but capped), so no
        # heavy computation can hide in module-level code.
        import_meter = Meter()
        import_meter.set_cap(IMPORT_WORK_CAP)
        factory, load_error = import_meter.call(_load_factory, entry, factory_name)
        if load_error is None and (factory is None or threading.active_count() != 1):
            load_error = "load_error"
    chunks = []
    while True:
        chunk = os.read(0, 1 << 16)
        if not chunk:
            break
        chunks.append(chunk)
    job = json.loads(b"".join(chunks))
    token = job.pop("token")
    inst = Instance.from_json(job["instance"])
    budget, work_cap = job["budget"], job["work_cap"]
    if load_error is not None:
        result = {"status": f"load_error:{load_error}", "path": [list(map(list, inst.starts))], "work": work_cap, "ticks": 0}
    elif kind == "builtin" and entry == "full_lacam":
        result = run_offline(inst, work_cap)
    elif kind == "builtin" and entry == "naive_rt_lacam":
        result = run_realtime(_FrozenNaiveRestart, inst, budget, work_cap)
    else:
        result = run_realtime(factory, inst, budget, work_cap)
    result["token"] = token
    with open(result_path, "w") as handle:
        handle.write(json.dumps(result))
        handle.flush()
        os.fsync(handle.fileno())
    # Skip atexit handlers and finalizers: nothing the planner registered may
    # run (unmetered) after the episode or touch the result.
    os._exit(WORKER_OK)


# ----------------------------------------------------------------------------
# Scoring (parent process)
# ----------------------------------------------------------------------------
def score_episode(inst, budget, work_cap, raw):
    """Recompute every number from the recorded path; failures get worst values."""
    horizon = horizon_for(budget, work_cap)
    path = _parse_path(raw.get("path"), inst.n_agents) if isinstance(raw, dict) else None
    work = raw.get("work") if isinstance(raw, dict) else None
    ok_work = type(work) is int and 0 <= work <= work_cap
    success = (
        isinstance(raw, dict)
        and raw.get("status") == "success"
        and ok_work
        and path is not None
        and len(path) - 1 <= horizon
        and legal_path(inst, path)
        and path[-1] == inst.goals
    )
    lb = max(1, inst.lower_bound)
    # Largest cost any execution that fits in the horizon can have.
    log_worst = math.log10(max(inst.n_agents * horizon, lb + 1) / lb)
    if success:
        cost = path_cost(inst, path)
        log_cost = min(log_worst, math.log10(max(cost, lb) / lb))
        score = 1.0 - log_cost / log_worst
        spent = work
    else:
        cost = None
        log_cost = log_worst
        score = 0.0
        spent = work_cap
    return {
        "instance": inst.name,
        "status": raw.get("status") if isinstance(raw, dict) else "missing",
        "success": bool(success),
        "realtime_score": score,
        "log_normalized_cost": log_cost,
        "log_planning_work": math.log10(1.0 + spent / 1000.0),
        "cost": cost,
        "lower_bound": inst.lower_bound,
        "work": work if ok_work else None,
        "ticks": len(path) - 1 if path else None,
    }


def _parse_path(raw, n_agents):
    if not isinstance(raw, list) or not raw:
        return None
    out = []
    for cfg in raw:
        parsed = _parse_config(cfg, n_agents)
        if parsed is None:
            return None
        out.append(parsed)
    return out


def summarize(rows):
    n = len(rows)
    return {
        "realtime_score": sum(r["realtime_score"] for r in rows) / n,
        "success_rate": sum(1 for r in rows if r["success"]) / n,
        "mean_log_normalized_cost": sum(r["log_normalized_cost"] for r in rows) / n,
        "mean_log_planning_work": sum(r["log_planning_work"] for r in rows) / n,
    }


def discover_planners(planners_dir):
    found = {}
    root = Path(planners_dir)
    if not root.is_absolute():
        root = WORKSPACE / root
    for manifest in sorted(root.glob("*.json")) if root.is_dir() else []:
        name = manifest.stem
        try:
            spec = json.loads(manifest.read_text())
        except (OSError, json.JSONDecodeError):
            spec = {}
        if isinstance(spec, dict) and isinstance(spec.get("name"), str) and spec["name"]:
            name = spec["name"]
        if name in BASELINES or name.startswith("_"):
            print(f"[eval] ignoring planner manifest {manifest.name}: name '{name}' is reserved", file=sys.stderr)
            continue
        entry = spec.get("entry") if isinstance(spec, dict) else None
        factory = spec.get("factory", "make_planner") if isinstance(spec, dict) else "make_planner"
        found[name] = (str(entry) if entry else "", str(factory))
    return found


def run_worker(source, kind, entry, factory, inst, budget, work_cap, scratch):
    """One episode in a fresh interpreter running this evaluator's in-memory source."""
    result_path = Path(scratch) / f"{secrets.token_hex(8)}.json"
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    env["RTMAPF_WORKSPACE"] = str(WORKSPACE)
    env.pop("PYTHONPATH", None)
    token = secrets.token_hex(16)
    job = json.dumps({"instance": inst.to_json(), "budget": budget, "work_cap": work_cap, "token": token}).encode()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", source, "--worker", kind, entry, factory, str(result_path)],
            input=job,
            cwd=str(WORKSPACE),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=WORKER_WALL_TIMEOUT,
            check=False,
        )
        raw = json.loads(result_path.read_text())
        if proc.returncode != WORKER_OK or not isinstance(raw, dict) or raw.get("token") != token:
            raw = {"status": "worker_failure"}
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        raw = {"status": "worker_failure"}
    finally:
        try:
            result_path.unlink()
        except OSError:
            pass
    return raw


def _default_jobs():
    try:
        n = len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        n = os.cpu_count() or 1
    return max(1, min(16, n))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker_main(sys.argv[2:])
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--planners-dir", default="outputs/planners")
    parser.add_argument("--out", default="scoring/scores_test.json")
    parser.add_argument("--details", default=None, help="optional per-instance record file")
    parser.add_argument("--methods-only", action="store_true", help="skip the frozen comparison rows")
    parser.add_argument("--jobs", type=int, default=_default_jobs())
    args = parser.parse_args()

    planners = discover_planners(args.planners_dir)
    entries = [(name, "manifest", entry, factory) for name, (entry, factory) in planners.items()]
    if not args.methods_only:
        entries += [(name, "builtin", name, "-") for name in BASELINES]

    family_instances = {fam: instances_for(fam) for fam in {e["family"] for e in EXPERIMENTS.values()}}
    tasks = []
    for exp_name, exp in EXPERIMENTS.items():
        for name, kind, entry, factory in entries:
            for inst in family_instances[exp["family"]]:
                tasks.append((exp_name, name, kind, entry, factory, inst, exp["budget"], exp["work_cap"]))

    scratch = WORKSPACE / "tmp" / f"eval_{SLICE}_{os.getpid()}"
    scratch.mkdir(parents=True, exist_ok=True)
    # Read once, before any planner runs: later edits to this file on disk
    # cannot change the code the workers execute.
    source = Path(__file__).read_text()

    def _run(task):
        exp_name, name, kind, entry, factory, inst, budget, work_cap = task
        raw = run_worker(source, kind, entry, factory, inst, budget, work_cap, scratch)
        return exp_name, name, score_episode(inst, budget, work_cap, raw)

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        records = list(pool.map(_run, tasks))
    try:
        scratch.rmdir()
    except OSError:
        pass

    per = {}
    for exp_name, name, row in records:
        per.setdefault(exp_name, {}).setdefault(name, []).append(row)
    scores = {"slice": SLICE, "experiments": {}}
    for exp_name, exp in EXPERIMENTS.items():
        results = {name: summarize(rows) for name, rows in sorted(per.get(exp_name, {}).items())}
        scores["experiments"][exp_name] = {
            "slice": SLICE,
            "budget_per_tick": exp["budget"],
            "work_cap": exp["work_cap"],
            "n_instances": len(family_instances[exp["family"]]),
            "results": results,
        }
    out = Path(args.out)
    if not out.is_absolute():
        out = WORKSPACE / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scores, indent=2) + "\n")
    if args.details:
        Path(args.details).write_text(json.dumps(per, indent=1) + "\n")
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
