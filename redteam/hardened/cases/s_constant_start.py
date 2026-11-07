"""Shortcut: never move (claims nothing, spends nothing)."""
import sys as _sys, pathlib as _pathlib; _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # noqa: E402,E702


class Stay:
    def step(self, config, clock):
        return config


def make_planner(instance):
    return Stay()
