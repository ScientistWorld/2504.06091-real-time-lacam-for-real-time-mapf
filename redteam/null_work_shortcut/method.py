"""Audit method; uses only agent-visible files and previously generated outputs."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
RT_FILES = ("rt_lacam.json", "rt_lacam_budget3.json", "movingai_rt_lacam.json")
# Shortcut: keep every path identical; change only the claimed search effort.
for filename in RT_FILES:
    path = Path("outputs/"+filename)
    obj = json.loads(path.read_text())
    for row in obj["results"]:
        row["expansions"] = None
    path.write_text(json.dumps(obj, indent=2))
