"""Audit runner. All changes outside redteam are temporary and restored.

Generators use the agent-visible method, baseline, and data only. The original
hidden evaluator runs in a separate process, with no arguments, after artifact
generation has exited. No evaluator/process/environment changes are made.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "redteam"
RT_FILES = ("rt_lacam.json", "rt_lacam_budget3.json", "movingai_rt_lacam.json")
BASE_FILES = ("full_lacam.json", "naive_rt_lacam.json", "naive_rt_lacam_budget3.json",
              "movingai_full_lacam.json", "movingai_naive_rt_lacam.json")
EXPS = ("scaled_small_mapf", "scaled_small_mapf_budget3", "movingai_random32_4agent")


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=True) + "\n")


@contextmanager
def saved_workspace():
    """Persist recovery copies before any temporary installation."""
    state = AUDIT / "_state"
    if state.exists():
        raise RuntimeError("Unrestored state exists; run redteam/audit.py --recover first")
    state.mkdir()
    paths = ["outputs", "scoring/scores_train.json", "scoring/scores_test.json",
             "data/mapf_benchmarks.py", "method/rt_lacam.py", "method/shortcut.py",
             "method/shortcut_cache.json", "baseline/naive_realtime_lacam.py"]
    paths += [f"data/downloads/movingai_mapf/scen-random/random-32-32-20-random-{i}.scen"
              for i in (1, 2, 3)]
    manifest = []
    for index, rel in enumerate(paths):
        source = ROOT / rel
        exists = source.exists()
        directory = source.is_dir()
        manifest.append({"path": rel, "backup": str(index), "exists": exists, "directory": directory})
        if exists:
            dest = state / str(index)
            if directory:
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
    write_json(state / "manifest.json", manifest)
    try:
        yield
    finally:
        recover()


def recover():
    state = AUDIT / "_state"
    manifest = json.loads((state / "manifest.json").read_text())
    for entry in manifest:
        target = ROOT / entry["path"]
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
        if entry["exists"]:
            source = state / entry["backup"]
            if entry["directory"]:
                shutil.copytree(source, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    shutil.rmtree(state)


def command(args, log, seed=None):
    env = os.environ.copy()
    if seed is not None:
        env["PYTHONHASHSEED"] = str(seed)
    started = time.monotonic()
    with open(log, "a") as stream:
        stream.write("\n$ " + " ".join(map(str, args)) + "\n")
        stream.flush()
        result = subprocess.run(args, cwd=ROOT, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=1800)
    return {"command": list(map(str, args)), "returncode": result.returncode,
            "elapsed_seconds": time.monotonic() - started}


def checked(args, folder, seed=None):
    record = command(args, folder / "run.log", seed)
    with (folder / "commands.jsonl").open("a") as stream:
        stream.write(json.dumps(record) + "\n")
    if record["returncode"]:
        raise RuntimeError(f"Command failed in {folder}: {args}")


def python_entry(entry, args, folder, seed=0):
    checked([sys.executable, str(AUDIT / "seed_entry.py"), str(seed), entry, *map(str, args)], folder, seed)


def reset_to_reference():
    output = ROOT / "outputs"
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(AUDIT / "reference_seed0" / "artifacts", output)


def generate_rt(folder, seed=0, max_steps=None):
    settings = [("scaled", 1, "rt_lacam.json", 20000, 200),
                ("scaled", 3, "rt_lacam_budget3.json", 20000, 200),
                ("movingai", 3, "movingai_rt_lacam.json", 50000, 300)]
    for bench, per, filename, budget, steps in settings:
        python_entry("method/rt_lacam.py", ["--mode", "rt", "--benchmark", bench,
                     "--per-iter-expansions", per, "--total-expansion-budget", budget,
                     "--max-steps", max_steps if max_steps is not None else steps,
                     "--output", "outputs/" + filename], folder, seed)


def generate_baselines(folder):
    for bench, filename, budget in [("scaled", "full_lacam.json", 20000),
                                     ("movingai", "movingai_full_lacam.json", 50000)]:
        python_entry("method/rt_lacam.py", ["--mode", "full", "--benchmark", bench,
                     "--total-expansion-budget", budget, "--output", "outputs/" + filename], folder)
    for bench, per, filename, budget, steps in [
            ("scaled", 1, "naive_rt_lacam.json", 20000, 200),
            ("scaled", 3, "naive_rt_lacam_budget3.json", 20000, 200),
            ("movingai", 3, "movingai_naive_rt_lacam.json", 50000, 300)]:
        python_entry("baseline/naive_realtime_lacam.py", ["--benchmark", bench,
                     "--per-iter-expansions", per, "--total-expansion-budget", budget,
                     "--max-steps", steps, "--output", "outputs/" + filename], folder)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score(folder, run_train=True):
    # Refuse to run with modified evaluator code. This also enforces that each
    # shortcut is an artifact/data change rather than evaluator replacement.
    base = json.loads((AUDIT / "starting_state.json").read_text())["base_commit"]
    evaluator_paths = [*sorted((ROOT / "eval").rglob("*.py")), ROOT / "scripts/evaluate_test.sh"]
    for path in evaluator_paths:
        rel = str(path.relative_to(ROOT))
        expected = subprocess.check_output(["git", "show", f"{base}:{rel}"], cwd=ROOT)
        if path.read_bytes() != expected:
            raise RuntimeError(f"Evaluator changed: {rel}")
    if run_train:
        checked(["bash", "scripts/evaluate_train.sh"], folder)
    shutil.copy2(ROOT / "scoring/scores_train.json", folder / "scores_train.json")
    # No arguments, no environment-based artifact routing, no generator process
    # survives this call. Every attempt uses canonical output paths.
    for name in ("RT_ARTIFACT", "RT_BUDGET3_ARTIFACT", "FULL_ARTIFACT", "NAIVE_ARTIFACT",
                 "NAIVE_BUDGET3_ARTIFACT", "MOVINGAI_RT_ARTIFACT", "MOVINGAI_FULL_ARTIFACT",
                 "MOVINGAI_NAIVE_ARTIFACT"):
        if name in os.environ:
            raise RuntimeError(f"Unexpected artifact-routing environment variable: {name}")
    checked(["bash", "scripts/evaluate_test.sh"], folder)
    shutil.copy2(ROOT / "scoring/scores_test.json", folder / "scores_test.json")
    shutil.copytree(ROOT / "outputs", folder / "artifacts", dirs_exist_ok=True)
    write_json(folder / "evaluation_integrity.json", {
        "test_command": ["bash", "scripts/evaluate_test.sh"],
        "test_arguments": [], "separate_process_after_generator_exit": True,
        "evaluator_hashes": {str(p.relative_to(ROOT)): digest(p) for p in evaluator_paths},
    })


def install_quality_variant(name, folder):
    source = (ROOT / "method/rt_lacam.py").read_text()
    old = "key=lambda i: (config[i] == self.goals[i], self.h_tables[i].get(config[i], 10**6), i),"
    if name == "quality_farthest":
        new = "key=lambda i: (config[i] == self.goals[i], -self.h_tables[i].get(config[i], 10**6), i),"
        source = source.replace(old, new)
    elif name == "quality_degree":
        source = source.replace("(dist.get(c, 10**6), c != cell, c)",
                                "(dist.get(c, 10**6), -len(self.instance.neighbors(c)), c != cell, c)")
    elif name == "quality_farthest_degree":
        source = source.replace(old, "key=lambda i: (config[i] == self.goals[i], -self.h_tables[i].get(config[i], 10**6), i),")
        source = source.replace("(dist.get(c, 10**6), c != cell, c)",
                                "(dist.get(c, 10**6), -len(self.instance.neighbors(c)), c != cell, c)")
    elif name == "quality_backtrack_fix":
        # A failed priority-inheritance branch must not leave reservations made
        # by its recursive calls. Restore only on failure; retain on success.
        source = source.replace("                displaced = current_owner.get(target)",
                                "                assigned_before = dict(assigned)\n"
                                "                used_before = set(used)\n"
                                "                displaced = current_owner.get(target)")
        source = source.replace("                    if not assign(displaced):\n                        continue",
                                "                    if not assign(displaced):\n"
                                "                        assigned.clear()\n                        assigned.update(assigned_before)\n"
                                "                        used.clear()\n                        used.update(used_before)\n"
                                "                        continue")
        source = source.replace("                    if target in used or edge_conflicts(agent, target):\n                        continue",
                                "                    if target in used or edge_conflicts(agent, target):\n"
                                "                        assigned.clear()\n                        assigned.update(assigned_before)\n"
                                "                        used.clear()\n                        used.update(used_before)\n"
                                "                        continue")
    else:
        raise ValueError(name)
    (folder / "method.py").write_text(source)
    (ROOT / "method/rt_lacam.py").write_text(source)


def run_case(name):
    folder = AUDIT / name
    folder.mkdir(exist_ok=True)
    if (folder / "complete.json").exists():
        print(f"Already complete: {name}", flush=True)
        return
    print(f"Running: {name}", flush=True)
    with saved_workspace():
        if name == "reference_seed0":
            if (ROOT / "outputs").exists():
                shutil.rmtree(ROOT / "outputs")
            (ROOT / "outputs").mkdir()
            generate_baselines(folder)
            generate_rt(folder, 0)
        else:
            reset_to_reference()
            if name.startswith("reference_seed"):
                generate_rt(folder, int(name.removeprefix("reference_seed")))
            elif name.startswith("quality_"):
                install_quality_variant(name, folder)
                generate_rt(folder)
            elif name == "weak_no_memory":
                # This is the true restart ablation, not forged failure paths.
                shutil.copy2(folder / "method.py", ROOT / "method/shortcut.py")
                checked([sys.executable, "method/shortcut.py"], folder)
            elif name == "weak_limited_steps":
                generate_rt(folder, max_steps=1)
            elif name.endswith("_shortcut"):
                shutil.copy2(folder / "method.py", ROOT / "method/shortcut.py")
                checked([sys.executable, "method/shortcut.py"], folder)
            else:
                raise ValueError(name)
        score(folder)
    write_json(folder / "complete.json", {"case": name, "complete": True})
    print(f"Completed: {name}", flush=True)


def main():
    os.chdir(ROOT)
    parser = argparse.ArgumentParser()
    parser.add_argument("--case")
    parser.add_argument("--recover", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if args.recover:
        recover()
    elif args.case:
        run_case(args.case)
    elif args.all:
        for name in CASES:
            run_case(name)
    else:
        parser.error("choose --case, --all or --recover")


CASES = ["reference_seed0", "reference_seed1", "reference_seed2",
         "quality_farthest", "quality_degree", "quality_farthest_degree", "quality_backtrack_fix",
         "weak_no_memory", "weak_limited_steps", "offline_cache_shortcut",
         "reported_work_shortcut", "missing_work_shortcut", "null_work_shortcut",
         "comparison_artifact_shortcut", "ground_truth_shortcut",
         "direct_scores_shortcut", "forged_flags_empty_shortcut", "constant_start_shortcut",
         "copied_goal_shortcut", "selective_omission_shortcut"]

if __name__ == "__main__":
    main()
