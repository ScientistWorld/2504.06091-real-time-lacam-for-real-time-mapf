"""Method-time (unmetered) cache build over every instance a scientist can see."""
import sys as _sys, pathlib as _pathlib; _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # noqa: E402,E702
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _common import full_plan  # noqa: E402
from s_public_cache import _CACHE_FILE, key  # noqa: E402

ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("visible_train_eval", ROOT / "eval" / "train" / "evaluate.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)
cache = {}
for fam in ("scaled", "movingai"):
    for inst in ev.instances_for(fam):
        view = inst.planner_view()
        plan = full_plan(view, max_attempts=20000)
        if plan:
            cache[key(view)] = [[list(c) for c in cfg] for cfg in plan]
_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
_CACHE_FILE.write_text(json.dumps(cache))
print(f"cached {len(cache)} visible instances")
