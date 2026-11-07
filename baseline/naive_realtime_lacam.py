"""Naive real-time LaCAM baseline: rebuild the lazy DFS from scratch every tick.

Implements the planner interface from briefing/evaluation.md. Register it with
``bash scripts/baseline.sh`` to score it on the train slice.
"""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from baseline.lacam_core import LazyLaCAM  # noqa: E402


class NaiveRestartPlanner:
    def __init__(self, instance: dict):
        self.instance = instance

    def step(self, config, clock):
        solver = LazyLaCAM(self.instance, start=config)
        solver.advance(clock)
        if solver.cursor == solver.root:
            return config
        return solver.path_to_root(solver.cursor)[1]


def make_planner(instance: dict) -> NaiveRestartPlanner:
    return NaiveRestartPlanner(instance)


class FullHorizonReplay:
    """Full-horizon LaCAM run inside the first tick, then replayed.

    Not a real-time method: its whole search is charged to the first decision.
    """

    def __init__(self, instance: dict):
        solver = LazyLaCAM(instance)
        while solver.cursor != solver.goals:
            if solver.dfs_attempt() == "exhausted":
                break
        self.plan = solver.path_to_root(solver.cursor) if solver.cursor == solver.goals else [solver.root]
        self.t = 0

    def step(self, config, clock):
        if self.t + 1 < len(self.plan):
            self.t += 1
            return self.plan[self.t]
        return config


def make_full_horizon_planner(instance: dict) -> FullHorizonReplay:
    return FullHorizonReplay(instance)
