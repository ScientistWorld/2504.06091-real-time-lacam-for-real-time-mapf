# Progress

## What Works

- Pure-Python Real-Time LaCAM implementation in `method/rt_lacam.py`.
- Full-horizon LaCAM comparator using the same lazy DFS machinery.
- Naive real-time restart baseline in `baseline/naive_realtime_lacam.py`.
- Method-independent evaluator in `eval/evaluate_mapf.py`.
- End-to-end scripts for method, baseline, evaluation, reproduction, and job
  submission.
- Audited on continuation: the implementation is identifiable as Real-Time
  LaCAM, not a surrogate. It maintains persistent lazy DFS state, uses
  constrained PIBT-style successor generation, executes one joint action per
  real-time iteration, and re-roots the tree after execution.

## Results

Previously verified compute jobs:

- Job `c3151de9-ae4` exited 0.
- It ran `scripts/run.sh`, regenerated scores, and passed
  `python validate.py --compare` inside the container.
- Job `1ac94747-97f` exited 0 after the budget-sweep expansion and passed the
  same validation inside the container.

Local expanded smoke-test command:

```bash
bash scripts/reproduce.sh
python validate.py --compare
```

Current local `scaled_small_mapf` scores with one expansion per real-time iteration after the PIBT-style generator update:

- `rt_lacam`: success_rate 1.000, valid_rate 1.000, mean_normalized_cost 2.972, mean_expansions 28.167.
- `full_lacam`: success_rate 1.000, valid_rate 1.000, mean_normalized_cost 1.417, mean_expansions 28.167.
- `naive_rt_lacam`: success_rate 0.167, valid_rate 0.167, mean_normalized_cost 1.000, mean_expansions 7.333.

Current local `scaled_small_mapf_budget3` scores with three expansions per real-time iteration:

- `rt_lacam`: success_rate 1.000, valid_rate 1.000, mean_normalized_cost 1.643, mean_expansions 28.167.
- `full_lacam`: success_rate 1.000, valid_rate 1.000, mean_normalized_cost 1.417, mean_expansions 28.167.
- `naive_rt_lacam`: success_rate 0.167, valid_rate 0.167, mean_normalized_cost 1.000, mean_expansions 219.000.

This supports the paper's core claim at scaled size: Real-Time LaCAM preserves
full-horizon success and search effort, while naive restart replanning can fail.

Audit fix:

- The previous lazy constraint schedule skipped part of the forced joint-action
  enumeration. It now follows the paper's block structure: 5 attempts
  constraining one agent, then 5^2 constraining two agents, continuing through
  all forced-prefix blocks. The local scores are unchanged, but the algorithmic
  coverage is now faithful.

## Remaining

- Optional future work: add larger standard MAPF benchmark maps and reproduce
  the learned-policy wrapper experiment from Figure 3.
- Awaiting compute-container verification for the corrected lazy constraint
  schedule.

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
- Paper implementation: PIBT as the one-step generator. This reproduction uses
  deterministic constrained PIBT-style recursive priority inheritance and
  backtracking with exhaustive fully constrained attempts, preserving the LaCAM
  lazy constrained DFS computation while keeping the environment compact.
