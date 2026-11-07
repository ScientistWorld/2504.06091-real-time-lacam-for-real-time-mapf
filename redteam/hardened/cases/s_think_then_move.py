"""Control: wait in place while the search runs within each tick's budget, then replay the plan."""
import sys as _sys, pathlib as _pathlib; _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # noqa: E402,E702
from _common import LazyLaCAM


class ThinkThenMove:
    def __init__(self, instance):
        self.solver = LazyLaCAM(instance)
        self.plan = None
        self.t = 0

    def step(self, config, clock):
        if self.plan is None:
            self.solver.advance(clock)
            if self.solver.cursor != self.solver.goals:
                return config
            self.plan = self.solver.path_to_root(self.solver.goals)
        if self.t + 1 < len(self.plan):
            self.t += 1
            return self.plan[self.t]
        return config


def make_planner(instance):
    return ThinkThenMove(instance)
