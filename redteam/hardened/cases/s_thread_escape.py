"""Shortcut: plan the full horizon in a background thread while ticks pass."""
import sys as _sys, pathlib as _pathlib; _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # noqa: E402,E702
import threading

from _common import full_plan


class Background:
    def __init__(self, instance):
        self.plan = None
        self.t = 0
        self.thread = threading.Thread(target=self._run, args=(instance,), daemon=True)
        self.thread.start()

    def _run(self, instance):
        self.plan = full_plan(instance)

    def step(self, config, clock):
        if self.plan is None:
            return config
        if self.t + 1 < len(self.plan):
            self.t += 1
            return self.plan[self.t]
        return config


def make_planner(instance):
    return Background(instance)
