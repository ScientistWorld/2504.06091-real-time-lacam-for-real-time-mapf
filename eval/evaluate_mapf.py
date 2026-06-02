"""Evaluate MAPF solver output artifacts without importing method code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data.mapf_benchmarks import (  # noqa: E402
    MAPFInstance,
    benchmark_suite,
    individual_optimal_cost,
    movingai_suite,
    path_is_legal,
    path_cost,
)


def _load_path(raw):
    return [tuple(tuple(cell) for cell in cfg) for cfg in raw]


def _failure_normalized_cost(instance: MAPFInstance) -> float:
    lower_bound = max(1, individual_optimal_cost(instance))
    return (2 * len(instance.free_cells()) * instance.n_agents) / lower_bound


def summarize_artifact(path: Path, instances: dict[str, MAPFInstance], allowed_instances: set[str]) -> dict:
    obj = json.loads(path.read_text())
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
            steps = None
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
            steps = len(plan) - 1 if plan else None
        rows.append(
            {
                "success": success,
                "valid": valid,
                "cost": cost,
                "normalized_cost": normalized_cost,
                "expansions": expansions,
                "steps": steps,
            }
        )
    norm = [r["normalized_cost"] for r in rows]
    expansion_values = [r["expansions"] for r in rows if r["expansions"] is not None]
    return {
        "success_rate": sum(1 for r in rows if r["success"]) / max(1, len(rows)),
        "valid_rate": sum(1 for r in rows if r["valid"]) / max(1, len(rows)),
        "coverage_rate": len(by_instance) / max(1, len(allowed_instances)),
        "mean_normalized_cost": statistics.mean(norm) if rows else None,
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
    parser.add_argument("--out", default="scoring/scores.json")
    args = parser.parse_args()

    scaled_instances = benchmark_suite()
    instances = {x.name: x for x in scaled_instances}
    scaled_names = {x.name for x in scaled_instances}
    movingai_paths = [Path(args.movingai_rt), Path(args.movingai_full), Path(args.movingai_naive)]
    movingai_names: set[str] = set()
    if any(p.exists() for p in movingai_paths):
        movingai_instances = movingai_suite()
        movingai_names = {x.name for x in movingai_instances}
        instances.update({x.name: x for x in movingai_instances})
    budget1 = {
        "rt_lacam": Path(args.rt),
        "full_lacam": Path(args.full),
        "naive_rt_lacam": Path(args.naive),
    }
    budget3 = {
        "rt_lacam": Path(args.rt_budget3),
        "full_lacam": Path(args.full),
        "naive_rt_lacam": Path(args.naive_budget3),
    }
    movingai = {
        "rt_lacam": Path(args.movingai_rt),
        "full_lacam": Path(args.movingai_full),
        "naive_rt_lacam": Path(args.movingai_naive),
    }
    summaries_budget1 = {
        name: summarize_artifact(p, instances, scaled_names)
        for name, p in budget1.items()
        if p.exists()
    }
    summaries_budget3 = {
        name: summarize_artifact(p, instances, scaled_names)
        for name, p in budget3.items()
        if p.exists()
    }
    summaries_movingai = {
        name: summarize_artifact(p, instances, movingai_names)
        for name, p in movingai.items()
        if p.exists()
    }

    scores = {
        "experiments": {
            "scaled_small_mapf": {
                "results": summaries_budget1,
            },
            "scaled_small_mapf_budget3": {
                "results": summaries_budget3,
            },
        }
    }
    if summaries_movingai:
        scores["experiments"]["movingai_random32_4agent"] = {
            "results": summaries_movingai,
        }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(scores, indent=2))
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
