"""Tabulate hardening case results (test and, where run, train).

D is a diagnostic only: sum over experiments of weight * sum(coefficient * metric)
using scoring/reference.json -- not the external ranking function.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ref = json.loads((ROOT / "scoring" / "reference.json").read_text())["experiments"]
summary = json.loads((Path(__file__).resolve().parent / "results" / "summary.json").read_text())
EXPS = list(ref)


def row(results, method):
    out, D = [], 0.0
    for e in EXPS:
        r = results[e][method]
        out.append(r)
        D += ref[e]["weight"] * sum(ref[e]["metrics"][k]["coefficient"] * v for k, v in r.items())
    return out, D


def table(split):
    print(f"\n### {split}\n")
    print("| case | realtime_score (A, B, C) | success (A, B, C) | log cost (A, B, C) | log work (A, B, C) | D |")
    print("|---|---|---|---|---|---|")
    for case, entry in summary.items():
        if split not in entry:
            continue
        res = entry[split]
        method = [m for m in res[EXPS[0]] if m not in ("full_lacam", "naive_rt_lacam")][0]
        rows, D = row(res, method)
        f = lambda k: ", ".join(f"{r[k]:.3f}" for r in rows)
        print(f"| {case} | {f('realtime_score')} | {f('success_rate')} | {f('mean_log_normalized_cost')} | {f('mean_log_planning_work')} | {D:.3f} |")
        if case == "reference" and "full_lacam" in res[EXPS[0]]:
            for b in ("full_lacam", "naive_rt_lacam"):
                rows, D = row(res, b)
                print(f"| ({b}, frozen row) | {f('realtime_score')} | {f('success_rate')} | {f('mean_log_normalized_cost')} | {f('mean_log_planning_work')} | {D:.3f} |")


table("test")
table("train")
