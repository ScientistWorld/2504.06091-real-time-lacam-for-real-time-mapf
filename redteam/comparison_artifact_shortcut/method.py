"""Audit method; uses only agent-visible files and previously generated outputs."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
RT_FILES = ("rt_lacam.json", "rt_lacam_budget3.json", "movingai_rt_lacam.json")
# Shortcut: replace the supposedly fixed comparators; candidate is unchanged.
for filename in ("full_lacam.json", "naive_rt_lacam.json", "naive_rt_lacam_budget3.json",
                 "movingai_full_lacam.json", "movingai_naive_rt_lacam.json"):
    path = Path("outputs/"+filename)
    obj = json.loads(path.read_text())
    for row in obj["results"]:
        row.update(path=[], success=False, valid=False, expansions=1000000000)
    path.write_text(json.dumps(obj, indent=2))
