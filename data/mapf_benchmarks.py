"""Small MAPF benchmark instances for Real-Time LaCAM reproduction.

The instances are intentionally compact so they can run in CPU smoke tests, but
they include narrow passages and opposing traffic to expose deadlock/livelock in
real-time replanning.
"""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from pathlib import Path
import json
import random
from typing import Iterable


Coord = tuple[int, int]


@dataclass(frozen=True)
class MAPFInstance:
    name: str
    width: int
    height: int
    obstacles: frozenset[Coord]
    starts: tuple[Coord, ...]
    goals: tuple[Coord, ...]

    @property
    def n_agents(self) -> int:
        return len(self.starts)

    def free_cells(self) -> list[Coord]:
        return [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in self.obstacles
        ]

    def neighbors(self, cell: Coord) -> list[Coord]:
        x, y = cell
        out = [cell]
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            nb = (x + dx, y + dy)
            if 0 <= nb[0] < self.width and 0 <= nb[1] < self.height and nb not in self.obstacles:
                out.append(nb)
        return out

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "obstacles": sorted(list(self.obstacles)),
            "starts": list(self.starts),
            "goals": list(self.goals),
        }

    @staticmethod
    def from_dict(obj: dict) -> "MAPFInstance":
        return MAPFInstance(
            name=obj["name"],
            width=int(obj["width"]),
            height=int(obj["height"]),
            obstacles=frozenset(tuple(p) for p in obj["obstacles"]),
            starts=tuple(tuple(p) for p in obj["starts"]),
            goals=tuple(tuple(p) for p in obj["goals"]),
        )


def shortest_path_distances(instance: MAPFInstance, goal: Coord) -> dict[Coord, int]:
    dist = {goal: 0}
    heap = [(0, goal)]
    while heap:
        d, cell = heappop(heap)
        if d != dist[cell]:
            continue
        for nb in instance.neighbors(cell):
            nd = d + 1
            if nd < dist.get(nb, 10**9):
                dist[nb] = nd
                heappush(heap, (nd, nb))
    return dist


def individual_optimal_cost(instance: MAPFInstance) -> int:
    total = 0
    for start, goal in zip(instance.starts, instance.goals):
        dist = shortest_path_distances(instance, goal)
        total += dist[start]
    return total


def validate_path(instance: MAPFInstance, path: list[tuple[Coord, ...]]) -> bool:
    if not path or path[0] != instance.starts:
        return False
    occupied = set(instance.free_cells())
    for config in path:
        if len(config) != instance.n_agents or len(set(config)) != len(config):
            return False
        if any(cell not in occupied for cell in config):
            return False
    for prev, cur in zip(path, path[1:]):
        for a, b in zip(prev, cur):
            if b not in instance.neighbors(a):
                return False
        for i in range(instance.n_agents):
            for j in range(i + 1, instance.n_agents):
                if prev[i] == cur[j] and prev[j] == cur[i]:
                    return False
    return path[-1] == instance.goals


def path_cost(instance: MAPFInstance, path: list[tuple[Coord, ...]]) -> int:
    cost = 0
    for prev, cur in zip(path, path[1:]):
        for i, (a, b) in enumerate(zip(prev, cur)):
            if a != instance.goals[i] or b != instance.goals[i]:
                cost += 1
    return cost


def _corridor_swap() -> MAPFInstance:
    free = {(x, 1) for x in range(7)} | {(3, 0), (3, 2)}
    obs = {(x, y) for y in range(3) for x in range(7)} - free
    return MAPFInstance(
        name="corridor_swap_2",
        width=7,
        height=3,
        obstacles=frozenset(obs),
        starts=((0, 1), (6, 1)),
        goals=((6, 1), (0, 1)),
    )


def _four_agent_cross() -> MAPFInstance:
    free = {(x, 3) for x in range(7)} | {(3, y) for y in range(7)}
    free |= {(2, 2), (4, 2), (2, 4), (4, 4)}
    obs = {(x, y) for y in range(7) for x in range(7)} - free
    return MAPFInstance(
        name="four_agent_cross",
        width=7,
        height=7,
        obstacles=frozenset(obs),
        starts=((0, 3), (6, 3), (3, 0), (3, 6)),
        goals=((6, 3), (0, 3), (3, 6), (3, 0)),
    )


def _random_dense(seed: int, idx: int) -> MAPFInstance:
    rng = random.Random(seed)
    width = height = 8
    starts: list[Coord] = []
    goals: list[Coord] = []
    while True:
        obs = {
            (x, y)
            for y in range(height)
            for x in range(width)
            if rng.random() < 0.16 and (x, y) not in {(0, 0), (7, 7)}
        }
        inst_tmp = MAPFInstance(f"random_dense_{idx}", width, height, frozenset(obs), (), ())
        cells = inst_tmp.free_cells()
        if len(cells) < 18:
            continue
        rng.shuffle(cells)
        starts = cells[:6]
        goals = cells[6:12]
        inst = MAPFInstance(f"random_dense_{idx}", width, height, frozenset(obs), tuple(starts), tuple(goals))
        if all(s in shortest_path_distances(inst, g) for s, g in zip(starts, goals)):
            return inst


def benchmark_suite() -> list[MAPFInstance]:
    instances = [_corridor_swap(), _four_agent_cross()]
    instances.extend(_random_dense(100 + i, i) for i in range(4))
    return instances


def write_benchmarks(path: str | Path) -> None:
    Path(path).write_text(json.dumps([x.to_dict() for x in benchmark_suite()], indent=2))


def load_benchmarks(path: str | Path | None = None) -> list[MAPFInstance]:
    if path is None:
        return benchmark_suite()
    return [MAPFInstance.from_dict(obj) for obj in json.loads(Path(path).read_text())]

