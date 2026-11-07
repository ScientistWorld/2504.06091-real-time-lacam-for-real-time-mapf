"""Lightweight evidence/restoration checks. Does not run a method or evaluator."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "redteam"
STATE = json.loads((AUDIT / "starting_state.json").read_text())
BASE = STATE["base_commit"]
EXPS = ("scaled_small_mapf", "scaled_small_mapf_budget3", "movingai_random32_4agent")
RT_FILES = ("rt_lacam.json", "rt_lacam_budget3.json", "movingai_rt_lacam.json")


def read(path):
    return json.loads(path.read_text())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def scores(case):
    return read(AUDIT / case / "scores_test.json")


def candidate(case):
    return {exp: row["results"]["rt_lacam"]
            for exp, row in scores(case)["experiments"].items()}


def main():
    folders = sorted(p.parent for p in AUDIT.glob("*/complete.json"))
    assert len(folders) == 31, len(folders)
    assert len([f for f in folders if f.name.endswith("_shortcut")]) == 12
    hashes = None
    total_commands = 0
    for folder in folders:
        assert (folder / "run.sh").is_file()
        commands = [json.loads(line) for line in (folder / "commands.jsonl").read_text().splitlines()]
        assert commands and all(c["returncode"] == 0 for c in commands), folder
        assert commands[-1]["command"] == ["bash", "scripts/evaluate_test.sh"], folder
        assert any(c["command"] == ["bash", "scripts/evaluate_train.sh"] for c in commands), folder
        total_commands += len(commands)
        integrity = read(folder / "evaluation_integrity.json")
        assert integrity["test_command"] == ["bash", "scripts/evaluate_test.sh"]
        assert integrity["test_arguments"] == []
        assert integrity["separate_process_after_generator_exit"] is True
        if hashes is None:
            hashes = integrity["evaluator_hashes"]
        assert hashes == integrity["evaluator_hashes"], folder
        read(folder / "scores_train.json")
        read(folder / "scores_test.json")

    for rel, expected_hash in hashes.items():
        original = git("show", f"{BASE}:{rel}")
        assert hashlib.sha256(original).hexdigest() == expected_hash, rel
        assert (ROOT / rel).read_bytes() == original, rel

    ref = candidate("reference_seed0")
    packaged = json.loads(git("show", f"{BASE}:scoring/scores_test.json"))
    assert all(scores(f"reference_seed{s}") == packaged for s in (0, 1, 2))
    summary = read(AUDIT / "summary.json")
    assert summary["reference_reproduces_packaged_test_scores_exactly"] is True
    assert summary["seed_diagnostic_spread"] == 0
    assert all(v == 0 for row in summary["seed_spread_max_minus_min"].values() for v in row.values())
    better = candidate("quality_rotations")
    for exp in EXPS:
        for metric in ("success_rate", "valid_rate", "coverage_rate"):
            assert better[exp][metric] >= ref[exp][metric]
        for metric in ("mean_normalized_cost", "mean_expansions", "duplicate_results"):
            assert better[exp][metric] <= ref[exp][metric]
    for exp in EXPS[:2]:
        assert better[exp]["mean_expansions"] < ref[exp]["mean_expansions"]
        assert better[exp]["mean_normalized_cost"] < ref[exp]["mean_normalized_cost"]
    for exp in EXPS:
        assert candidate("weak_no_memory")[exp]["success_rate"] < ref[exp]["success_rate"]
        assert candidate("weak_limited_steps")[exp]["success_rate"] == 0
    diagnostic = "coefficient_weighted_diagnostic_not_external_rank"
    assert summary["cases"]["weak_limited_steps"][diagnostic] > summary["cases"]["reference_seed0"][diagnostic]

    for case, expansion_value in (("reported_work_shortcut", -1000000000),
                                   ("missing_work_shortcut", 0), ("null_work_shortcut", None)):
        rows = candidate(case)
        for exp in EXPS:
            assert rows[exp]["mean_expansions"] == expansion_value
            assert {k: v for k, v in rows[exp].items() if k != "mean_expansions"} == {
                k: v for k, v in ref[exp].items() if k != "mean_expansions"}
        for filename in RT_FILES:
            original_rows = read(AUDIT / "reference_seed0/artifacts" / filename)["results"]
            changed_rows = read(AUDIT / case / "artifacts" / filename)["results"]
            assert [x["path"] for x in original_rows] == [x["path"] for x in changed_rows]

    assert candidate("comparison_artifact_shortcut") == ref
    assert scores("direct_scores_shortcut") == packaged
    for exp in EXPS:
        for method in ("full_lacam", "naive_rt_lacam"):
            row = scores("comparison_artifact_shortcut")["experiments"][exp]["results"][method]
            assert row["success_rate"] == row["valid_rate"] == 0
        ground = candidate("ground_truth_shortcut")[exp]
        assert ground["success_rate"] == ground["valid_rate"] == ground["coverage_rate"] == 1
        assert ground["mean_normalized_cost"] == ground["mean_expansions"] == 0
    assert candidate("train_scope_shortcut") == {EXPS[2]: ref[EXPS[2]]}
    assert set(scores("train_scope_shortcut")["experiments"][EXPS[2]]["results"]) == {"rt_lacam"}
    for tie in ("quality_backtrack_fix", "quality_goal_traffic"):
        assert candidate(tie) == ref
    for filename, full in zip(RT_FILES, ("full_lacam.json", "full_lacam.json", "movingai_full_lacam.json")):
        offline_rows = read(AUDIT / "offline_cache_shortcut/artifacts" / filename)["results"]
        baseline_rows = read(AUDIT / "reference_seed0/artifacts" / full)["results"]
        assert offline_rows == baseline_rows

    # Exclude only audit output, protocol action, and dirty paths present at start.
    exclusions = ["redteam/**", "REDTEAM.md", "action.yaml", "README.md", "manifest.json"]
    exclusions += [f"trajectory/turn_{i:04d}_raw.jsonl" for i in range(1, 6)]
    diff = git("diff", "--name-only", BASE, "--", ".", *[f":(exclude){p}" for p in exclusions]).decode().splitlines()
    assert not diff, f"Unexpected changes outside audit: {diff}"
    assert not (AUDIT / "_state").exists()
    assert not (ROOT / "method/shortcut.py").exists()
    assert not (ROOT / "method/shortcut_cache.json").exists()
    assert (ROOT / "scripts/run.sh").read_bytes() == git("show", f"{BASE}:scripts/run.sh")

    result = {"cases": len(folders), "shortcuts": 12, "commands_with_exit_zero": total_commands,
              "reference_seed_spread": 0, "packaged_reference_reproduced": True,
              "original_evaluator_hashes": hashes,
              "unexpected_changes_outside_audit": diff,
              "preexisting_dirty_paths_preserved": STATE["initial_status"],
              "protocol_exception": "action.yaml carries the final done signal",
              "all_checks_passed": True}
    (AUDIT / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
