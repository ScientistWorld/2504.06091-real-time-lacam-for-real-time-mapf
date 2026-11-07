"""Shared helpers for the hardening shortcut cases (method-side code)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from method.rt_lacam import LazyLaCAM, RealTimeLaCAM  # noqa: E402,F401


def full_plan(instance, max_attempts=None):
    """Unbounded full-horizon LaCAM search; returns the joint plan or None."""
    solver = LazyLaCAM(instance)
    n = 0
    while solver.cursor != solver.goals:
        if solver.dfs_attempt() == "exhausted":
            return None
        n += 1
        if max_attempts is not None and n >= max_attempts:
            return None
    return solver.path_to_root(solver.goals)


class Replay:
    def __init__(self, plan, fallback=None):
        self.plan = plan
        self.t = 0

    def step(self, config, clock):
        if self.plan and self.t + 1 < len(self.plan):
            self.t += 1
            return self.plan[self.t]
        return config
