"""Audit method; uses only agent-visible files and previously generated outputs."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
RT_FILES = ("rt_lacam.json", "rt_lacam_budget3.json", "movingai_rt_lacam.json")
from baseline.naive_realtime_lacam import run_naive
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
