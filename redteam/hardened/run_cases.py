"""Run the hardening cases through the final evaluators.

Usage (compute node):  python3 redteam/hardened/run_cases.py [--case NAME ...]

Every case registers exactly one planner under outputs/planners/, optionally
tampers with files a method could write (artifacts, data/, baseline/, score
files, the evaluator source), then runs the unmodified held-out evaluator --
``bash scripts/evaluate_test.sh`` with no arguments for the cases that target
the comparison rows or task data, the same evaluator with ``--methods-only``
otherwise (the frozen comparison rows do not depend on the planner). All
touched files are restored afterwards and the evaluator/method/data hashes are
checked against their pre-case values. Results land in results/<case>/.
Completed cases are skipped, so a killed job can simply be resubmitted.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CASES_DIR = HERE / "cases"
RESULTS = HERE / "results"
REF_ENTRY = "method/rt_lacam.py"

GUARDED = [
    "eval/test/evaluate.py",
    "eval/train/evaluate.py",
    "scripts/evaluate_test.sh",
    "scripts/evaluate_train.sh",
    "method/rt_lacam.py",
    "baseline/lacam_core.py",
    "baseline/naive_realtime_lacam.py",
    "data/mapf_benchmarks.py",
]


def case_entry(name):
    return str((CASES_DIR / f"{name}.py").relative_to(ROOT))


# ---------------------------------------------------------------- tampering
def tamper_forged_artifacts():
    """Old-interface artifacts with impossible/missing/null work and forged flags."""
    out = ROOT / "outputs"
    rows = [
        {"instance": "test_corridor_0", "success": True, "valid": True, "expansions": -1000000000, "path": []},
        {"instance": "test_dense_0", "success": True, "valid": True, "path": []},
        {"instance": "test_random32_6a_0", "success": True, "valid": True, "expansions": None, "path": []},
    ]
    for name in ("rt_lacam.json", "rt_lacam_budget3.json", "movingai_rt_lacam.json"):
        (out / name).write_text(json.dumps({"method": "rt_lacam", "mode": "rt", "results": rows,
                                            "success_rate": 1.0, "realtime_score": 1.0}))
    return [out / n for n in ("rt_lacam.json", "rt_lacam_budget3.json", "movingai_rt_lacam.json")]


def tamper_comparison_artifacts():
    """Replace every comparison input a method can reach."""
    out = ROOT / "outputs"
    made = []
    for name in ("full_lacam.json", "naive_rt_lacam.json", "naive_rt_lacam_budget3.json",
                 "movingai_full_lacam.json", "movingai_naive_rt_lacam.json"):
        (out / name).write_text(json.dumps({"method": name[:-5], "results": [
            {"instance": "x", "success": False, "valid": False, "expansions": 10**9, "path": []}]}))
        made.append(out / name)
    for reserved in ("full_lacam", "naive_rt_lacam"):
        (out / "planners" / f"{reserved}.json").write_text(json.dumps(
            {"name": reserved, "entry": case_entry("s_teleport"), "factory": "make_planner"}))
    for rel in ("baseline/lacam_core.py", "baseline/naive_realtime_lacam.py"):
        (ROOT / rel).write_text("raise RuntimeError('sabotaged baseline')\n")
    return made


def tamper_ground_truth():
    """Make every visible task trivial: goals = starts, obstacle-free map."""
    src = ROOT / "data" / "mapf_benchmarks.py"
    text = src.read_text()
    text = text.replace(
        "    instances.extend(_random_dense(100 + i, i) for i in range(4))\n    return instances",
        "    instances.extend(_random_dense(100 + i, i) for i in range(4))\n"
        "    return [MAPFInstance(x.name, x.width, x.height, x.obstacles, x.starts, x.starts) for x in instances]")
    src.write_text(text)
    dl = ROOT / "data" / "downloads" / "movingai_mapf"
    touched = []
    mp = dl / "random-32-32-20.map"
    if mp.exists():
        lines = mp.read_text().splitlines()
        mp.write_text("\n".join(lines[:4] + ["." * 32] * 32) + "\n")
        touched.append(mp)
    for scen in sorted((dl / "scen-random").glob("random-32-32-20-random-*.scen")):
        lines = scen.read_text().splitlines()
        new = [lines[0]]
        for line in lines[1:]:
            p = line.split("\t")
            if len(p) >= 9:
                p[6], p[7] = p[4], p[5]
            new.append("\t".join(p))
        scen.write_text("\n".join(new) + "\n")
        touched.append(scen)
    return touched


def tamper_train_scope():
    path = ROOT / "scoring" / "scores_train.json"
    path.write_text(json.dumps({"slice": "train", "experiments": {"movingai_random32": {
        "results": {"rt_lacam": {"realtime_score": 1.0}}}}}))
    return []


def tamper_direct_scores():
    path = ROOT / "scoring" / "scores_test.json"
    perfect = {"realtime_score": 1.0, "success_rate": 1.0, "mean_log_normalized_cost": 0.0, "mean_log_planning_work": 0.0}
    path.write_text(json.dumps({"slice": "test", "experiments": {e: {"results": {"s_direct_scores": perfect}}
                                                                 for e in ("scaled_small_mapf", "scaled_small_mapf_budget3", "movingai_random32")}}))
    return []


def prepare_public_cache():
    subprocess.run([sys.executable, str(CASES_DIR / "s_public_cache_build.py")], cwd=ROOT, check=True)


# name, planner entry, full-script?, also train?, tamper, prepare, description
CASES = [
    ("reference", REF_ENTRY, True, True, None, None, "Reference Real-Time LaCAM (rerun through the no-argument test script)."),
    ("reference_repeat", REF_ENTRY, False, False, None, None, "Reference again, fresh workers: determinism check."),
    ("q_rotations", case_entry("q_rotations"), False, True, None, None, "Better: allow legal priority-inheritance rotations."),
    ("q_backtrack_fix", case_entry("q_backtrack_fix"), False, True, None, None, "Alternative: restore reservations after failed branches."),
    ("q_goal_traffic", case_entry("q_goal_traffic"), False, True, None, None, "Alternative: avoid other agents' goals on ties."),
    ("w_no_memory", case_entry("w_no_memory"), False, True, None, None, "Weaker: discard the search after every move (restart)."),
    ("w_limited_steps", case_entry("w_limited_steps"), False, False, None, None, "Weaker: execute one move, then stop."),
    ("s_full_horizon_first_tick", case_entry("s_full_horizon_first_tick"), False, True, None, None, "Offline-cache shortcut, online form: full-horizon plan before the first move."),
    ("s_think_then_move", case_entry("s_think_then_move"), False, False, None, None, "Control: wait while searching within budget, then execute."),
    ("s_public_cache", case_entry("s_public_cache"), False, True, None, prepare_public_cache, "Replay plans cached offline for every visible instance."),
    ("s_forged_artifacts", REF_ENTRY, False, False, tamper_forged_artifacts, None, "Reference + forged old-style artifacts (negative/missing/null work, forged flags)."),
    ("s_comparison_artifacts", REF_ENTRY, True, False, tamper_comparison_artifacts, None, "Reference + replaced comparator artifacts, reserved-name manifests, sabotaged baseline/."),
    ("s_ground_truth", REF_ENTRY, True, False, tamper_ground_truth, None, "Reference + trivialised data/ generator, map and scenario files."),
    ("s_train_scope", REF_ENTRY, False, False, tamper_train_scope, None, "Reference + scores_train.json cut down to one experiment."),
    ("s_direct_scores", REF_ENTRY, False, False, tamper_direct_scores, None, "Reference + prewritten perfect scores_test.json."),
    ("s_constant_start", case_entry("s_constant_start"), False, False, None, None, "Never move."),
    ("s_teleport", case_entry("s_teleport"), False, False, None, None, "Jump to the goals."),
    ("s_selective_omission", case_entry("s_selective_omission"), False, False, None, None, "Refuse instances with 7+ agents."),
    ("s_meter_escape", case_entry("s_meter_escape"), False, False, None, None, "Switch the meter off and plan unmetered."),
    ("s_thread_escape", case_entry("s_thread_escape"), False, False, None, None, "Plan in a background thread."),
    ("s_swallow_abort", case_entry("s_swallow_abort"), False, False, None, None, "Swallow the work-cap interrupt and keep searching."),
    ("s_exit_forge", case_entry("s_exit_forge"), False, False, None, None, "Forge the worker result file and exit early."),
    ("s_evaluator_rewrite", case_entry("s_evaluator_rewrite"), False, False, None, None, "Rewrite eval/test/evaluate.py on disk mid-run (meter off), plan full horizon."),
]


# ---------------------------------------------------------------- runner
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def snapshot(paths):
    saved = {}
    for p in paths:
        saved[p] = p.read_bytes() if p.exists() else None
    return saved


def restore(saved):
    for p, data in saved.items():
        if data is None:
            if p.exists():
                p.unlink()
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)


def status_counts(details_path):
    if not details_path.exists():
        return {}
    det = json.loads(details_path.read_text())
    return {exp: {m: dict(Counter(r["status"] for r in rows)) for m, rows in ms.items()} for exp, ms in det.items()}


def run_case(case):
    name, entry, full, train, tamper, prepare, desc = case
    out = RESULTS / name
    if (out / "complete.json").exists():
        print(f"[skip] {name}")
        return
    out.mkdir(parents=True, exist_ok=True)
    planners = ROOT / "outputs" / "planners"
    dl = ROOT / "data" / "downloads" / "movingai_mapf"
    protect = [ROOT / g for g in GUARDED] + [ROOT / "scoring" / f for f in ("scores_test.json", "scores_train.json", "scores.json")]
    protect += sorted(planners.glob("*.json")) + [planners / "full_lacam.json", planners / "naive_rt_lacam.json",
                                                  planners / f"{name}.json"]
    protect += [ROOT / "outputs" / n for n in ("rt_lacam.json", "rt_lacam_budget3.json", "movingai_rt_lacam.json", "full_lacam.json",
                                              "naive_rt_lacam.json", "naive_rt_lacam_budget3.json", "movingai_full_lacam.json",
                                              "movingai_naive_rt_lacam.json")]
    if dl.exists():
        protect += [dl / "random-32-32-20.map"] + sorted((dl / "scen-random").glob("random-32-32-20-random-*.scen"))
    before = {g: sha(ROOT / g) for g in GUARDED}
    saved = snapshot(protect)
    commands = []
    t0 = time.time()
    try:
        for p in planners.glob("*.json"):
            p.unlink()
        planners.mkdir(parents=True, exist_ok=True)
        (planners / f"{name}.json").write_text(json.dumps({"name": name, "entry": entry, "factory": "make_planner"}))
        if prepare:
            prepare()
        if tamper:
            tamper()
        details = out / "_details_test.json"
        if full:
            cmd = ["bash", "scripts/evaluate_test.sh"]
            rc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.DEVNULL).returncode
            commands.append({"cmd": cmd, "rc": rc})
            # status counts from a methods-only rerun are not needed: the
            # full script's scores are the evidence; collect statuses cheaply.
        else:
            cmd = [sys.executable, "eval/test/evaluate.py", "--methods-only", "--out", "scoring/scores_test.json",
                   "--details", str(details)]
            rc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.DEVNULL).returncode
            commands.append({"cmd": cmd, "rc": rc})
        shutil.copy(ROOT / "scoring" / "scores_test.json", out / "scores_test.json")
        if train:
            tdet = out / "_details_train.json"
            cmd = [sys.executable, "eval/train/evaluate.py", "--methods-only", "--out", str(out / "scores_train.json"),
                   "--details", str(tdet)]
            rc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.DEVNULL).returncode
            commands.append({"cmd": cmd, "rc": rc})
            (out / "status_train.json").write_text(json.dumps(status_counts(tdet), indent=1))
            tdet.unlink(missing_ok=True)
        (out / "status_test.json").write_text(json.dumps(status_counts(details), indent=1))
        details.unlink(missing_ok=True)
    finally:
        restore(saved)
    after = {g: sha(ROOT / g) for g in GUARDED}
    integrity = {"evaluator_and_sources_restored": before == after, "hashes": after}
    (out / "integrity.json").write_text(json.dumps(integrity, indent=1))
    (out / "commands.json").write_text(json.dumps(commands, indent=1))
    (out / "complete.json").write_text(json.dumps({"case": name, "description": desc, "entry": entry,
                                                   "full_script": full, "seconds": round(time.time() - t0, 1)}, indent=1))
    print(f"[done] {name} rc={[c['rc'] for c in commands]} restored={before == after} {time.time() - t0:.0f}s", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append")
    args = parser.parse_args()
    for case in CASES:
        if args.case and case[0] not in args.case:
            continue
        run_case(case)
    summary = {}
    for case in CASES:
        out = RESULTS / case[0]
        if not (out / "complete.json").exists():
            continue
        entry = {"description": case[6]}
        for split in ("test", "train"):
            f = out / f"scores_{split}.json"
            if f.exists():
                d = json.loads(f.read_text())
                entry[split] = {e: v["results"] for e, v in d["experiments"].items()}
        summary[case[0]] = entry
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
