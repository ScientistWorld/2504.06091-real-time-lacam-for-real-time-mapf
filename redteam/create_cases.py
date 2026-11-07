"""Write standalone, agent-visible-input-only audit variants and run wrappers."""
from pathlib import Path

HERE = Path(__file__).resolve().parent

HEADER = '''"""Audit method; uses only agent-visible files and previously generated outputs."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
RT_FILES = ("rt_lacam.json", "rt_lacam_budget3.json", "movingai_rt_lacam.json")
'''

scripts = {}
scripts['weak_no_memory'] = HEADER + '''from baseline.naive_realtime_lacam import run_naive
from data.mapf_benchmarks import benchmark_suite, movingai_suite
for bench, per, filename, budget, steps in [
    ("scaled", 1, RT_FILES[0], 20000, 200),
    ("scaled", 3, RT_FILES[1], 20000, 200),
    ("movingai", 3, RT_FILES[2], 50000, 300),
]:
    instances = benchmark_suite() if bench == "scaled" else movingai_suite()
    obj = {"method":"rt_lacam", "mode":"rt", "benchmark":bench,
           "per_iter_expansions":per, "total_expansion_budget":budget,
           "results":[run_naive(inst, per, budget, steps) for inst in instances]}
    Path("outputs/"+filename).write_text(json.dumps(obj, indent=2))
'''

scripts['offline_cache_shortcut'] = HEADER + '''# Shortcut: solve every public deterministic task offline, then replay cached plans.
# There is no incremental real-time planner in the submitted method.
from baseline.lacam_core import run_full
from data.mapf_benchmarks import benchmark_suite, movingai_suite
cache = {}
for bench, instances, budget in [("scaled",benchmark_suite(),20000),
                                  ("movingai",movingai_suite(),50000)]:
    cache[bench] = [run_full(inst, budget) for inst in instances]
cache_path = Path("method/shortcut_cache.json")
cache_path.write_text(json.dumps(cache))
# This is the entire replay method. The true offline effort remains reported;
# the shortcut does not require falsifying expansion counts.
cache = json.loads(cache_path.read_text())
for bench, per, filename in [("scaled",1,RT_FILES[0]), ("scaled",3,RT_FILES[1]),
                              ("movingai",3,RT_FILES[2])]:
    obj = {"method":"rt_lacam", "mode":"rt", "benchmark":bench,
           "per_iter_expansions":per, "results":cache[bench]}
    Path("outputs/"+filename).write_text(json.dumps(obj, indent=2))
'''

for name, operation in {
    'reported_work_shortcut': 'row["expansions"] = -1000000000',
    'missing_work_shortcut': 'row.pop("expansions", None)',
    'null_work_shortcut': 'row["expansions"] = None',
}.items():
    scripts[name] = HEADER + '''# Shortcut: keep every path identical; change only the claimed search effort.
for filename in RT_FILES:
    path = Path("outputs/"+filename)
    obj = json.loads(path.read_text())
    for row in obj["results"]:
        ''' + operation + '''
    path.write_text(json.dumps(obj, indent=2))
'''

scripts['comparison_artifact_shortcut'] = HEADER + '''# Shortcut: replace the supposedly fixed comparators; candidate is unchanged.
for filename in ("full_lacam.json", "naive_rt_lacam.json", "naive_rt_lacam_budget3.json",
                 "movingai_full_lacam.json", "movingai_naive_rt_lacam.json"):
    path = Path("outputs/"+filename)
    obj = json.loads(path.read_text())
    for row in obj["results"]:
        row.update(path=[], success=False, valid=False, expansions=1000000000)
    path.write_text(json.dumps(obj, indent=2))
'''

scripts['ground_truth_shortcut'] = HEADER + '''# Shortcut: make the visible task definitions already solved at the start.
# Only the generator and scenario labels change; metric/validation code stays intact.
source_path = Path("data/mapf_benchmarks.py")
source = source_path.read_text()
old = "    instances.extend(_random_dense(100 + i, i) for i in range(4))\\n    return instances"
new = ("    instances.extend(_random_dense(100 + i, i) for i in range(4))\\n"
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
            line = "\\t".join(parts)
        changed.append(line)
    path.write_text("\\n".join(changed)+"\\n")
from data.mapf_benchmarks import benchmark_suite, movingai_suite
for bench, per, filename in [("scaled",1,RT_FILES[0]), ("scaled",3,RT_FILES[1]),
                              ("movingai",3,RT_FILES[2])]:
    instances = benchmark_suite() if bench == "scaled" else movingai_suite()
    obj = {"method":"rt_lacam", "mode":"rt", "benchmark":bench, "per_iter_expansions":per,
           "results":[{"instance":x.name, "path":[x.starts], "expansions":0} for x in instances]}
    Path("outputs/"+filename).write_text(json.dumps(obj, indent=2))
'''

scripts['direct_scores_shortcut'] = HEADER + '''# Shortcut attempt: directly prewrite an excellent hidden score file.
# The genuine hidden evaluator should overwrite it from the unchanged paths.
Path("scoring/scores_test.json").write_text(json.dumps({"slice":"test", "shortcut_sentinel":True,
    "experiments":{name:{"results":{"rt_lacam":{"success_rate":1,"valid_rate":1,
        "coverage_rate":1,"mean_normalized_cost":0,"mean_expansions":-1000000000}}}
    for name in ("scaled_small_mapf","scaled_small_mapf_budget3","movingai_random32_4agent")}}))
'''

scripts['forged_flags_empty_shortcut'] = HEADER + '''# Shortcut attempt: empty paths and fabricated perfect success/cost fields.
for filename in RT_FILES:
    path = Path("outputs/"+filename)
    obj = json.loads(path.read_text())
    for row in obj["results"]:
        row.update(path=[], success=True, valid=True, steps=0,
                   sum_of_costs=-1000000000, normalized_cost=-1000000000, expansions=0)
    path.write_text(json.dumps(obj, indent=2))
'''

scripts['constant_start_shortcut'] = HEADER + '''# Shortcut attempt: return only the initial state, doing no planning.
for filename in RT_FILES:
    path = Path("outputs/"+filename)
    obj = json.loads(path.read_text())
    for row in obj["results"]:
        row.update(path=row["path"][:1], expansions=0)
    path.write_text(json.dumps(obj, indent=2))
'''

scripts['copied_goal_shortcut'] = HEADER + '''# Shortcut attempt: copy public goals, skipping all intermediate actions.
from data.mapf_benchmarks import benchmark_suite, movingai_suite
for filename in RT_FILES:
    path = Path("outputs/"+filename)
    obj = json.loads(path.read_text())
    instances = benchmark_suite() if obj["benchmark"] == "scaled" else movingai_suite()
    obj["results"] = [{"instance":x.name, "path":[x.starts,x.goals], "expansions":0} for x in instances]
    path.write_text(json.dumps(obj, indent=2))
'''

scripts['selective_omission_shortcut'] = HEADER + '''# Shortcut attempt: keep one known easy row and omit the remaining tasks.
for filename in RT_FILES:
    path = Path("outputs/"+filename)
    obj = json.loads(path.read_text())
    obj["results"] = sorted(obj["results"], key=lambda r:r["normalized_cost"] or 1e9)[:1]
    path.write_text(json.dumps(obj, indent=2))
'''

cases = ['reference_seed0','reference_seed1','reference_seed2','quality_farthest','quality_degree',
         'quality_farthest_degree','quality_backtrack_fix','weak_no_memory','weak_limited_steps',*scripts]
for name in dict.fromkeys(cases):
    folder = HERE / name
    folder.mkdir(exist_ok=True)
    (folder/'run.sh').write_text('#!/bin/bash\nset -euo pipefail\ncd /home/user\npython3 redteam/audit.py --case '+name+'\n')
    if name in scripts:
        (folder/'method.py').write_text(scripts[name])
