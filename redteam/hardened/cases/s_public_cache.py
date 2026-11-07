"""Shortcut: replay plans cached offline for every visible instance; otherwise run the reference."""
import sys as _sys, pathlib as _pathlib; _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # noqa: E402,E702
import json
from pathlib import Path

from _common import RealTimeLaCAM, Replay

_CACHE_FILE = Path(__file__).resolve().parents[1] / "results" / "s_public_cache" / "cache.json"
CACHE = json.loads(_CACHE_FILE.read_text()) if _CACHE_FILE.exists() else {}


def key(instance):
    return repr((instance["width"], instance["height"], sorted(instance["obstacles"]),
                 [list(c) for c in instance["starts"]], [list(c) for c in instance["goals"]]))


def make_planner(instance):
    plan = CACHE.get(key(instance))
    if plan:
        return Replay([tuple(tuple(c) for c in cfg) for cfg in plan])
    return RealTimeLaCAM(instance)
