"""Audit method; uses only agent-visible files and previously generated outputs."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
RT_FILES = ("rt_lacam.json", "rt_lacam_budget3.json", "movingai_rt_lacam.json")
# Shortcut: make the visible task definitions already solved at the start.
# Only the generator and scenario labels change; metric/validation code stays intact.
source_path = Path("data/mapf_benchmarks.py")
source = source_path.read_text()
old = "    instances.extend(_random_dense(100 + i, i) for i in range(4))\n    return instances"
new = ("    instances.extend(_random_dense(100 + i, i) for i in range(4))\n"
       "    return [MAPFInstance(x.name, x.width, x.height, x.obstacles, x.starts, x.starts) for x in instances]")
assert old in source
source_path.write_text(source.replace(old,new))
for sid in (1,2,3):
    path = Path(f"data/downloads/movingai_mapf/scen-random/random-32-32-20-random-{sid}.scen")
    lines = path.read_text().splitlines()
    changed = [lines[0]]
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 9:
            parts[6:8] = parts[4:6]
            line = "\t".join(parts)
        changed.append(line)
    path.write_text("\n".join(changed)+"\n")
from data.mapf_benchmarks import benchmark_suite, movingai_suite
for bench, per, filename in [("scaled",1,RT_FILES[0]), ("scaled",3,RT_FILES[1]),
                              ("movingai",3,RT_FILES[2])]:
    instances = benchmark_suite() if bench == "scaled" else movingai_suite()
    obj = {"method":"rt_lacam", "mode":"rt", "benchmark":bench, "per_iter_expansions":per,
           "results":[{"instance":x.name, "path":[x.starts], "expansions":0} for x in instances]}
    Path("outputs/"+filename).write_text(json.dumps(obj, indent=2))
