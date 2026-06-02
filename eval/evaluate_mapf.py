"""Evaluate MAPF solver output artifacts without importing method code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data.mapf_benchmarks import MAPFInstance, benchmark_suite, validate_path, path_cost, individual_optimal_cost  # noqa: E402


def _load_path(raw):
    return [tuple(tuple(cell) for cell in cfg) for cfg in raw]


def summarize_artifact(path: Path, instances: dict[str, MAPFInstance]) -> dict:
    obj = json.loads(path.read_text())
    rows = []
    for res in obj["results"]:
        inst = instances[res["instance"]]
        plan = _load_path(res.get("path", []))
        valid = validate_path(inst, plan)
        success = bool(valid and plan[-1] == inst.goals) if plan else False
        cost = path_cost(inst, plan) if valid else None
        rows.append(
            {
                "success": success,
                "valid": valid,
                "cost": cost,
                "normalized_cost": cost / max(1, individual_optimal_cost(inst)) if cost is not None else None,
                "expansions": res.get("expansions", 0),
                "steps": len(plan) - 1 if plan else None,
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
    parser.add_argument("--full", default="outputs/full_lacam.json")
    parser.add_argument("--naive", default="outputs/naive_rt_lacam.json")
    parser.add_argument("--out", default="scoring/scores.json")
    args = parser.parse_args()

    instances = {x.name: x for x in benchmark_suite()}
    artifacts = {
        "rt_lacam": Path(args.rt),
        "full_lacam": Path(args.full),
        "naive_rt_lacam": Path(args.naive),
    }
    summaries = {name: summarize_artifact(p, instances) for name, p in artifacts.items() if p.exists()}

    scores = {
        "experiments": {
            "scaled_small_mapf": {
                "results": summaries,
            }
        }
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(scores, indent=2))
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()

