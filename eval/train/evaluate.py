"""Train-slice MAPF evaluator for method output artifacts.

This file intentionally duplicates the held-out evaluator instead of importing
from eval/test so the visible train slice is self-contained.
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


SLICE = "train"
SCALED_INSTANCES = {
    "corridor_swap_2",
    "random_dense_0",
    "random_dense_2",
}
MOVINGAI_INSTANCES = {
    "movingai_random-32-32-20_random_1_4a",
    "movingai_random-32-32-20_random_3_4a",
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


def summarize_artifact(path: Path, instances: dict[str, MAPFInstance], allowed_instances: set[str]) -> dict:
    obj = _load_json(path)
    rows = []
    for res in obj["results"]:
        if res["instance"] not in allowed_instances:
            continue
        inst = instances[res["instance"]]
        plan = _load_path(res.get("path", []))
        valid = path_is_legal(inst, plan)
        success = bool(valid and plan[-1] == inst.goals) if plan else False
        cost = path_cost(inst, plan) if valid else None
        rows.append(
            {
                "success": success,
                "valid": valid,
                "cost": cost,
                "normalized_cost": cost / max(1, individual_optimal_cost(inst)) if cost is not None else None,
                "expansions": res.get("expansions", 0),
            }
        )
    solved = [r for r in rows if r["success"]]
    norm = [r["normalized_cost"] for r in solved if r["normalized_cost"] is not None]
    return {
        "success_rate": sum(1 for r in rows if r["success"]) / max(1, len(rows)),
        "valid_rate": sum(1 for r in rows if r["valid"]) / max(1, len(rows)),
        "mean_normalized_cost": statistics.mean(norm) if norm else None,
        "mean_expansions": statistics.mean(r["expansions"] for r in rows) if rows else None,
        "instances": len(rows),
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
    parser.add_argument("--out", default="scoring/scores_train.json")
    args = parser.parse_args()

    artifacts = _discover_artifacts(args)
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
