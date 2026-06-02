"""Held-out MAPF evaluator for method output artifacts.

This file intentionally duplicates the train evaluator instead of importing
from eval/train so the held-out slice is independently runnable.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from data.mapf_benchmarks import (  # noqa: E402
    MAPFInstance,
    benchmark_suite,
    individual_optimal_cost,
    movingai_suite,
    path_cost,
    path_is_legal,
)


SLICE = "test"
SCALED_INSTANCES = {
    "four_agent_cross",
    "random_dense_1",
    "random_dense_3",
}
MOVINGAI_INSTANCES = {
    "movingai_random-32-32-20_random_2_4a",
}


def _load_path(raw):
    return [tuple(tuple(cell) for cell in cfg) for cfg in raw]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _method_name(path: Path, obj: dict) -> str:
    method = obj.get("method")
    if isinstance(method, str) and method:
        return method
    return path.stem


def _explicit_artifacts(args: argparse.Namespace) -> dict[str, dict[str, Path]]:
    return {
        "scaled_small_mapf": {
            "rt_lacam": Path(args.rt),
            "full_lacam": Path(args.full),
            "naive_rt_lacam": Path(args.naive),
        },
        "scaled_small_mapf_budget3": {
            "rt_lacam": Path(args.rt_budget3),
            "full_lacam": Path(args.full),
            "naive_rt_lacam": Path(args.naive_budget3),
        },
        "movingai_random32_4agent": {
            "rt_lacam": Path(args.movingai_rt),
            "full_lacam": Path(args.movingai_full),
            "naive_rt_lacam": Path(args.movingai_naive),
        },
    }


def _discover_artifacts(args: argparse.Namespace) -> dict[str, dict[str, Path]]:
    artifacts = {
        exp: {name: path for name, path in methods.items() if path.exists()}
        for exp, methods in _explicit_artifacts(args).items()
    }
    known_paths = {path.resolve() for methods in artifacts.values() for path in methods.values()}

    for path in sorted(Path(args.outputs_dir).glob("*.json")):
        if path.resolve() in known_paths:
            continue
        try:
            obj = _load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(obj.get("results"), list):
            continue
        method = _method_name(path, obj)
        benchmark = obj.get("benchmark", "scaled")
        mode = obj.get("mode")
        per_iter = obj.get("per_iter_expansions")
        stem = path.stem.lower()

        if benchmark == "movingai":
            artifacts["movingai_random32_4agent"].setdefault(method, path)
        elif mode == "full":
            artifacts["scaled_small_mapf"].setdefault(method, path)
            artifacts["scaled_small_mapf_budget3"].setdefault(method, path)
        elif per_iter == 3 or "budget3" in stem:
            artifacts["scaled_small_mapf_budget3"].setdefault(method, path)
        else:
            artifacts["scaled_small_mapf"].setdefault(method, path)

    return artifacts


def _instances_for(paths: list[Path]) -> dict[str, MAPFInstance]:
    instances = {x.name: x for x in benchmark_suite()}
    if any(p.exists() and _artifact_uses_movingai(p) for p in paths):
        instances.update({x.name: x for x in movingai_suite()})
    return instances


def _artifact_uses_movingai(path: Path) -> bool:
    try:
        return _load_json(path).get("benchmark") == "movingai"
    except (OSError, json.JSONDecodeError):
        return path.name.startswith("movingai_")


def _required_methods(train_scores_path: Path) -> dict[str, set[str]]:
    if not train_scores_path.exists():
        return {}
    train_scores = _load_json(train_scores_path)
    required: dict[str, set[str]] = {}
    for exp_name, exp in train_scores.get("experiments", {}).items():
        results = exp.get("results", {}) if isinstance(exp, dict) else {}
        if isinstance(results, dict):
            required[exp_name] = {name for name in results if not name.startswith("_")}
    return required


def _restrict_to_train_methods(
    artifacts: dict[str, dict[str, Path]],
    required: dict[str, set[str]],
) -> dict[str, dict[str, Path]]:
    if not required:
        return artifacts
    missing: dict[str, list[str]] = {}
    restricted: dict[str, dict[str, Path]] = {}
    for exp_name, method_names in required.items():
        available = artifacts.get(exp_name, {})
        restricted[exp_name] = {}
        for method in sorted(method_names):
            if method in available:
                restricted[exp_name][method] = available[method]
            else:
                missing.setdefault(exp_name, []).append(method)
    if missing:
        details = "; ".join(f"{exp}: {methods}" for exp, methods in sorted(missing.items()))
        raise FileNotFoundError(
            "Held-out evaluation could not find artifacts for train-scored methods: "
            f"{details}"
        )
    return restricted


def _failure_normalized_cost(instance: MAPFInstance) -> float:
    lower_bound = max(1, individual_optimal_cost(instance))
    return (2 * len(instance.free_cells()) * instance.n_agents) / lower_bound


def summarize_artifact(path: Path, instances: dict[str, MAPFInstance], allowed_instances: set[str]) -> dict:
    obj = _load_json(path)
    by_instance = {}
    duplicate_results = 0
    for res in obj["results"]:
        name = res["instance"]
        if name not in allowed_instances:
            continue
        if name in by_instance:
            duplicate_results += 1
            continue
        by_instance[name] = res

    rows = []
    for name in sorted(allowed_instances):
        inst = instances[name]
        res = by_instance.get(name)
        if res is None:
            valid = False
            success = False
            cost = None
            normalized_cost = _failure_normalized_cost(inst)
            expansions = None
        else:
            plan = _load_path(res.get("path", []))
            valid = path_is_legal(inst, plan)
            success = bool(valid and plan[-1] == inst.goals) if plan else False
            cost = path_cost(inst, plan) if valid else None
            normalized_cost = (
                cost / max(1, individual_optimal_cost(inst))
                if success and cost is not None
                else _failure_normalized_cost(inst)
            )
            expansions = res.get("expansions", 0)
        rows.append(
            {
                "success": success,
                "valid": valid,
                "cost": cost,
                "normalized_cost": normalized_cost,
                "expansions": expansions,
            }
        )
    norm = [r["normalized_cost"] for r in rows]
    expansion_values = [r["expansions"] for r in rows if r["expansions"] is not None]
    return {
        "success_rate": sum(1 for r in rows if r["success"]) / max(1, len(rows)),
        "valid_rate": sum(1 for r in rows if r["valid"]) / max(1, len(rows)),
        "coverage_rate": len(by_instance) / max(1, len(allowed_instances)),
        "mean_normalized_cost": statistics.mean(norm),
        "mean_expansions": statistics.mean(expansion_values) if expansion_values else None,
        "duplicate_results": duplicate_results,
        "instances": len(allowed_instances),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rt", default="outputs/rt_lacam.json")
    parser.add_argument("--rt-budget3", default="outputs/rt_lacam_budget3.json")
    parser.add_argument("--full", default="outputs/full_lacam.json")
    parser.add_argument("--naive", default="outputs/naive_rt_lacam.json")
    parser.add_argument("--naive-budget3", default="outputs/naive_rt_lacam_budget3.json")
    parser.add_argument("--movingai-rt", default="outputs/movingai_rt_lacam.json")
    parser.add_argument("--movingai-full", default="outputs/movingai_full_lacam.json")
    parser.add_argument("--movingai-naive", default="outputs/movingai_naive_rt_lacam.json")
    parser.add_argument("--outputs-dir", default="outputs")
    parser.add_argument("--train-scores", default="scoring/scores_train.json")
    parser.add_argument("--out", default="scoring/scores_test.json")
    args = parser.parse_args()

    artifacts = _restrict_to_train_methods(
        _discover_artifacts(args),
        _required_methods(Path(args.train_scores)),
    )
    all_paths = [path for methods in artifacts.values() for path in methods.values()]
    instances = _instances_for(all_paths)

    split_by_experiment = {
        "scaled_small_mapf": SCALED_INSTANCES,
        "scaled_small_mapf_budget3": SCALED_INSTANCES,
        "movingai_random32_4agent": MOVINGAI_INSTANCES,
    }
    scores = {"slice": SLICE, "experiments": {}}
    for exp_name, methods in artifacts.items():
        summaries = {
            method: summarize_artifact(path, instances, split_by_experiment[exp_name])
            for method, path in sorted(methods.items())
            if path.exists()
        }
        if summaries:
            scores["experiments"][exp_name] = {"slice": SLICE, "results": summaries}

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(scores, indent=2))
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
