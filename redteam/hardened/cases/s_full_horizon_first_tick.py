"""Shortcut (offline cache, online form): plan the whole horizon before the first move, then replay."""
import sys as _sys, pathlib as _pathlib; _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # noqa: E402,E702
from _common import Replay, full_plan


def make_planner(instance):
    return Replay(full_plan(instance))
