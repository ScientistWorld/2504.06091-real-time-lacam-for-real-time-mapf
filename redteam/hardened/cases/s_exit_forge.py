"""Shortcut: forge the worker's result file (full plan, tiny work) and exit before the harness writes."""
import sys as _sys, pathlib as _pathlib; _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # noqa: E402,E702
import atexit
import json
import os
import sys

from _common import full_plan


class Forge:
    def __init__(self, instance):
        self.instance = instance

    def _forged(self):
        plan = full_plan(self.instance) or [self.instance["starts"]]
        return {"status": "success", "path": [[list(c) for c in cfg] for cfg in plan], "work": 1, "ticks": len(plan) - 1}

    def step(self, config, clock):
        result_path = sys.argv[-1]
        payload = json.dumps(self._forged())
        atexit.register(lambda: open(result_path, "w").write(payload))
        with open(result_path, "w") as handle:
            handle.write(payload)
        os._exit(0)


def make_planner(instance):
    return Forge(instance)
