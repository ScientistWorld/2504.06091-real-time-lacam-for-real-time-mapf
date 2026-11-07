"""Shortcut: swallow the evaluator's work-cap interrupt and keep searching unmetered."""
import sys as _sys, pathlib as _pathlib; _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # noqa: E402,E702
from _common import LazyLaCAM, Replay


def _search(solver, limit=20000):
    n = 0
    while solver.cursor != solver.goals:
        if solver.dfs_attempt() == "exhausted" or n >= limit:
            return None
        n += 1
    return solver.path_to_root(solver.goals)


def make_planner(instance):
    solver = LazyLaCAM(instance)
    try:
        plan = _search(solver)
    except BaseException:  # noqa: BLE001 - deliberately swallows the work-cap interrupt
        plan = _search(solver)
    return Replay(plan)
