"""Naive real-time LaCAM baseline: re-run lazy LaCAM from scratch each step."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data.mapf_benchmarks import benchmark_suite, individual_optimal_cost, movingai_suite, path_is_legal, path_cost  # noqa: E402
from baseline.lacam_core import LazyLaCAM  # noqa: E402


def run_naive(instance, per_iter_expansions: int, total_expansion_budget: int, max_steps: int) -> dict:
    executed = [instance.starts]
    expansions = 0
    while executed[-1] != instance.goals and len(executed) <= max_steps and expansions < total_expansion_budget:
        solver = LazyLaCAM(instance, start=executed[-1])
        solver.advance(per_iter_expansions)
        expansions += solver.expansions
        partial = solver.path_to_root(solver.cursor)
        if len(partial) < 2:
            break
        executed.append(partial[1])
    legal = path_is_legal(instance, executed)
    success = legal and executed[-1] == instance.goals
    return {
        "instance": instance.name,
        "success": bool(success),
        "valid": bool(legal),
        "steps": len(executed) - 1,
        "sum_of_costs": path_cost(instance, executed) if legal else None,
        "normalized_cost": (path_cost(instance, executed) / max(1, individual_optimal_cost(instance))) if legal else None,
        "expansions": expansions,
        "path": [[list(c) for c in cfg] for cfg in executed],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", choices=["scaled", "movingai"], default="scaled")
    parser.add_argument("--output", default="outputs/naive_rt_lacam.json")
    parser.add_argument("--per-iter-expansions", type=int, default=1)
    parser.add_argument("--total-expansion-budget", type=int, default=20000)
    parser.add_argument("--max-steps", type=int, default=200)
    args = parser.parse_args()
    instances = benchmark_suite() if args.benchmark == "scaled" else movingai_suite()
    results = [
        run_naive(inst, args.per_iter_expansions, args.total_expansion_budget, args.max_steps)
        for inst in instances
    ]
    out = {
        "method": "naive_rt_lacam",
        "mode": "naive_rt",
        "benchmark": args.benchmark,
        "per_iter_expansions": args.per_iter_expansions,
        "total_expansion_budget": args.total_expansion_budget,
        "results": results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
