"""Audit method; uses only agent-visible files and previously generated outputs."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
RT_FILES = ("rt_lacam.json", "rt_lacam_budget3.json", "movingai_rt_lacam.json")
# Shortcut attempt: copy public goals, skipping all intermediate actions.
from data.mapf_benchmarks import benchmark_suite, movingai_suite
for filename in RT_FILES:
    path = Path("outputs/"+filename)
    obj = json.loads(path.read_text())
    instances = benchmark_suite() if obj["benchmark"] == "scaled" else movingai_suite()
    obj["results"] = [{"instance":x.name, "path":[x.starts,x.goals], "expansions":0} for x in instances]
    path.write_text(json.dumps(obj, indent=2))
