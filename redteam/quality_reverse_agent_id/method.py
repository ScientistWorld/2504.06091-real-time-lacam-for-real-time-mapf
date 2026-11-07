"""Real-Time LaCAM reproduction.

This module implements the computation described in Liang et al. (2025):
lazy DFS over joint MAPF configurations, a constrained one-step MAPF generator,
persistent search state across planning iterations, and re-rooting after each
executed action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import argparse
import json
from pathlib import Path
import sys
from typing import Iterable

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data.mapf_benchmarks import (  # noqa: E402
    MAPFInstance,
    benchmark_suite,
    individual_optimal_cost,
    movingai_suite,
    path_is_legal,
    path_cost,
    shortest_path_distances,
    validate_path,
)


Coord = tuple[int, int]
Config = tuple[Coord, ...]
ACTIONS = ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1))


@dataclass
class Node:
    config: Config
    parent: Config | None = None
    attempts: int = 0
    generated: set[Config] = field(default_factory=set)
    exhausted: bool = False


class LazyLaCAM:
    def __init__(self, instance: MAPFInstance, start: Config | None = None):
        self.instance = instance
        self.start = start or instance.starts
        self.goals = instance.goals
        self.h_tables = [shortest_path_distances(instance, g) for g in self.goals]
        self.nodes: dict[Config, Node] = {self.start: Node(self.start, None)}
        self.root = self.start
        self.cursor = self.start
        self.expansions = 0
        self.max_attempts = sum(5 ** k for k in range(1, instance.n_agents + 1))

    def is_goal(self, config: Config) -> bool:
        return config == self.goals

    def _ordered_actions(self, agent: int, cell: Coord) -> list[Coord]:
        nbs = self.instance.neighbors(cell)
        dist = self.h_tables[agent]
        return sorted(nbs, key=lambda c: (dist.get(c, 10**6), c != cell, c))

    def _forced_prefix(self, attempt: int) -> dict[int, Coord]:
        """Map a lazy attempt counter to LaCAM-style agent action constraints."""
        if attempt == 0:
            return {}
        prefix, value = self._constraint_block(attempt)
        forced = {}
        for agent in range(prefix):
            digit = value % 5
            value //= 5
            actions = self._ordered_actions(agent, self.nodes[self.cursor].config[agent])
            forced[agent] = actions[digit % len(actions)]
        return forced

    @property
    def cursor_node(self) -> Node:
        return self.nodes[self.cursor]

    def _constraint_block(self, attempt: int) -> tuple[int, int]:
        """Return (forced-prefix length, block-local index) for an attempt.

        Attempt 0 is unconstrained. Attempts after that follow the LaCAM lazy
        schedule: 5 attempts constraining agent 0, then 5^2 attempts
        constraining agents 0..1, and so on. Keeping the block-local index
        separate is important; otherwise some joint-action combinations are
        skipped and the lazy DFS no longer covers the intended search space.
        """
        value = attempt - 1
        for prefix in range(1, self.instance.n_agents + 1):
            block_size = 5 ** prefix
            if value < block_size:
                return prefix, value
            value -= block_size
        return self.instance.n_agents, (5 ** self.instance.n_agents) - 1

    def _candidate_from_forced(self, config: Config, forced: dict[int, Coord]) -> Config | None:
        """Generate one constrained successor with PIBT-style priority inheritance.

        LaCAM only requires a one-step MAPF generator that can honor fixed
        actions for a prefix of agents. PIBT assigns agents in priority order;
        when an agent wants a currently occupied cell, the occupant inherits
        priority and is recursively moved out of the way, with backtracking if
        no collision-free continuation exists.
        """
        current_owner = {cell: i for i, cell in enumerate(config)}
        assigned: dict[int, Coord] = {}
        used: set[Coord] = set()
        visiting: set[int] = set()

        def edge_conflicts(agent: int, target: Coord) -> bool:
            for other, other_target in assigned.items():
                if config[agent] == other_target and config[other] == target:
                    return True
            return False

        def assign(agent: int) -> bool:
            if agent in assigned:
                return True
            if agent in visiting:
                return False
            visiting.add(agent)
            choices = [forced[agent]] if agent in forced else self._ordered_actions(agent, config[agent])
            for target in choices:
                if target not in self.instance.neighbors(config[agent]) or target in used:
                    continue
                if edge_conflicts(agent, target):
                    continue

                displaced = current_owner.get(target)
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

        order = sorted(
            range(self.instance.n_agents),
            key=lambda i: (config[i] == self.goals[i], -i),
        )
        for agent in order:
            if not assign(agent):
                return None
        nxt = tuple(assigned[i] for i in range(self.instance.n_agents))
        return nxt if self._valid_transition(config, nxt) else None

    def _valid_transition(self, config: Config, nxt: Config) -> bool:
        if len(set(nxt)) != len(nxt):
            return False
        for i, (a, b) in enumerate(zip(config, nxt)):
            if b not in self.instance.neighbors(a):
                return False
        for i in range(len(config)):
            for j in range(i + 1, len(config)):
                if config[i] == nxt[j] and config[j] == nxt[i]:
                    return False
        return True

    def _next_successor(self, node: Node) -> Config | None:
        while node.attempts <= self.max_attempts:
            attempt = node.attempts
            node.attempts += 1
            if attempt == 0:
                forced = {}
            else:
                prefix, value = self._constraint_block(attempt)
                forced = {}
                for agent in range(prefix):
                    digit = value % 5
                    value //= 5
                    actions = self._ordered_actions(agent, node.config[agent])
                    forced[agent] = actions[digit % len(actions)]
            succ = self._candidate_from_forced(node.config, forced)
            if succ is not None and succ not in node.generated:
                node.generated.add(succ)
                return succ
        node.exhausted = True
        return None

    def advance(self, expansion_budget: int) -> Config | None:
        """Continue the lazy DFS for a bounded number of generated successors."""
        for _ in range(max(0, expansion_budget)):
            if self.is_goal(self.cursor):
                return self.cursor
            node = self.nodes[self.cursor]
            succ = self._next_successor(node)
            self.expansions += 1
            if succ is None:
                if node.parent is None:
                    return self.cursor if self.is_goal(self.cursor) else None
                self.cursor = node.parent
                continue
            if succ not in self.nodes:
                self.nodes[succ] = Node(succ, node.config)
            self.cursor = succ
            if self.is_goal(succ):
                return succ
        return self.cursor

    def path_to_root(self, config: Config | None = None) -> list[Config]:
        config = config or self.cursor
        path = [config]
        seen = {config}
        while self.nodes[config].parent is not None:
            config = self.nodes[config].parent  # type: ignore[assignment]
            if config in seen:
                raise RuntimeError("parent cycle during path reconstruction")
            seen.add(config)
            path.append(config)
        path.reverse()
        return path

    def solve_full(self, expansion_budget: int) -> list[Config] | None:
        for _ in range(expansion_budget):
            goal = self.advance(1)
            if goal is not None and self.is_goal(goal):
                return self.path_to_root(goal)
        return None

    def reroot_to_child(self, child: Config) -> None:
        """Reverse parent pointers along root -> child, as in Real-Time LaCAM."""
        if child == self.root:
            return
        path = self.path_to_root(child)
        if path[0] != self.root or path[-1] != child:
            raise RuntimeError("cannot reroot to a configuration outside the current tree path")
        for parent, node in zip(path, path[1:]):
            self.nodes[parent].parent = node
        self.nodes[child].parent = None
        self.root = child


def run_realtime(instance: MAPFInstance, per_iter_expansions: int, total_expansion_budget: int, max_steps: int) -> dict:
    solver = LazyLaCAM(instance)
    executed = [instance.starts]
    total_exp = 0
    goal_found = False
    while executed[-1] != instance.goals and len(executed) <= max_steps and total_exp < total_expansion_budget:
        before = solver.expansions
        target = solver.advance(per_iter_expansions)
        total_exp += solver.expansions - before
        partial = solver.path_to_root(target or solver.cursor)
        if len(partial) < 2:
            # No forward edge available from the current root; spend more budget next round.
            continue
        nxt = partial[1]
        solver.reroot_to_child(nxt)
        executed.append(nxt)
        if nxt == instance.goals:
            goal_found = True
            break
    legal = path_is_legal(instance, executed)
    success = legal and executed[-1] == instance.goals
    return {
        "instance": instance.name,
        "success": bool(success),
        "valid": bool(legal),
        "steps": len(executed) - 1,
        "sum_of_costs": path_cost(instance, executed) if legal else None,
        "normalized_cost": (path_cost(instance, executed) / max(1, individual_optimal_cost(instance))) if legal else None,
        "expansions": total_exp,
        "expanded_nodes": len(solver.nodes),
        "path": [[list(c) for c in cfg] for cfg in executed],
    }


def run_full(instance: MAPFInstance, expansion_budget: int) -> dict:
    solver = LazyLaCAM(instance)
    path = solver.solve_full(expansion_budget)
    valid = path is not None and validate_path(instance, path)
    return {
        "instance": instance.name,
        "success": bool(valid),
        "valid": bool(valid),
        "steps": len(path) - 1 if path else None,
        "sum_of_costs": path_cost(instance, path) if path and valid else None,
        "normalized_cost": (path_cost(instance, path) / max(1, individual_optimal_cost(instance))) if path and valid else None,
        "expansions": solver.expansions,
        "expanded_nodes": len(solver.nodes),
        "path": [[list(c) for c in cfg] for cfg in path] if path else [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "rt"], default="rt")
    parser.add_argument("--benchmark", choices=["scaled", "movingai"], default="scaled")
    parser.add_argument("--output", default="outputs/rt_lacam.json")
    parser.add_argument("--per-iter-expansions", type=int, default=1)
    parser.add_argument("--total-expansion-budget", type=int, default=20000)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--instances", default="all")
    args = parser.parse_args()

    instances = benchmark_suite() if args.benchmark == "scaled" else movingai_suite()
    if args.instances != "all":
        keep = set(args.instances.split(","))
        instances = [x for x in instances if x.name in keep]

    results = []
    for inst in instances:
        if args.mode == "full":
            results.append(run_full(inst, args.total_expansion_budget))
        else:
            results.append(run_realtime(inst, args.per_iter_expansions, args.total_expansion_budget, args.max_steps))

    out = {
        "method": "rt_lacam" if args.mode == "rt" else "full_lacam",
        "mode": args.mode,
        "benchmark": args.benchmark,
        "per_iter_expansions": args.per_iter_expansions,
        "total_expansion_budget": args.total_expansion_budget,
        "results": results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
