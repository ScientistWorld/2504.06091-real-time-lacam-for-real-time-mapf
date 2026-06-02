# Progress

## What Works

- Pure-Python Real-Time LaCAM implementation in `method/rt_lacam.py`.
- Full-horizon LaCAM comparator using the same lazy DFS machinery.
- Naive real-time restart baseline in `baseline/naive_realtime_lacam.py`.
- Method-independent evaluator in `eval/evaluate_mapf.py`.
- End-to-end scripts for method, baseline, evaluation, reproduction, and job
  submission.

## Results

Local smoke-test command:

```bash
bash scripts/reproduce.sh
```

Current `scaled_small_mapf` scores:

- `rt_lacam`: success_rate 1.000, valid_rate 1.000, mean_normalized_cost 1.842, mean_expansions 14.5.
- `full_lacam`: success_rate 1.000, valid_rate 1.000, mean_normalized_cost 1.211, mean_expansions 14.5.
- `naive_rt_lacam`: success_rate 0.667, valid_rate 0.667, mean_normalized_cost 1.114, mean_expansions 40.333.

This supports the paper's core claim at scaled size: Real-Time LaCAM preserves
full-horizon success and search effort, while naive restart replanning can fail.

## Remaining

- Run the packaged reproduction as a compute job.
- If budget allows after job verification, add more instances or larger maps for
  `core_claim_plus`.

## Issues

- The paper reports most Figure 2 values graphically/qualitatively rather than
  as exact tables. `scoring/reference.json` therefore encodes the central
  qualitative targets on the scaled benchmark rather than exact benchmark
  numbers from the figure.

## Deviations from Paper

- Paper data: standard MAPF benchmark subset with 25 scenes per map. This
  reproduction uses deterministic scaled grid instances generated in
  `data/mapf_benchmarks.py` to keep jobs short and self-contained.
- Paper time budget: millisecond wall-clock per-iteration cutoffs and 60-second
  cumulative timeout. This reproduction uses per-iteration successor expansion
  budgets and total expansion budgets as hardware-independent equivalents.
- Paper implementation: full PIBT as the one-step generator. This reproduction
  uses a deterministic constrained PIBT-style greedy generator with exhaustive
  fully constrained attempts, preserving the LaCAM lazy constrained DFS
  computation while reducing implementation complexity.
