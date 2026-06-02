# Evaluation Targets

## Primary: realtime_mapf_benchmark
Tests whether a real-time MAPF system solves the standard benchmark scenes under strict per-iteration planning budgets.
- **Metric**: success_rate_gap_vs_full_horizon (lower is better)
- **Metric**: cumulative_planning_time_ratio_vs_full_horizon (lower is better, with parity as the target)
- **Metric**: normalized_solution_cost_factor_vs_full_horizon (lower is better)
- **How to run**: evaluate the same benchmark maps/scenes and agent-count settings as the paper, with the same cumulative timeout and per-iteration cutoffs.

## Constraint: realtime_validity_and_budget
Checks that the reported success is achieved under the real-time protocol rather than by planning full-horizon paths before execution or exceeding the per-step budget.
- **Metric**: cumulative_timeout_s (fixed-condition metric)
- **Metric**: min_cutoff_ms (fixed-condition metric)
- **Metric**: max_cutoff_ms (fixed-condition metric)
- **Metric**: collision_failures (lower is better)
- **How to run**: enforce the configured cutoff at every planning/execution iteration, count timed-out runs as failures, and reject any execution trace with vertex or edge collisions.

## Ablation: naive_replanning_baseline
Tests whether preserving useful planning state across real-time iterations matters, by comparing against a real-time baseline that restarts its search each step.
- **Metric**: success_rate_gap_vs_full_horizon (lower is better)
- **Metric**: cumulative_planning_time_ratio_vs_full_horizon (lower is better)
- **How to run**: run the restarted-search baseline under the same maps, scenes, cutoffs, and cumulative timeout as the primary benchmark.

## Secondary: learned_policy_wrapper
Tests whether the real-time planning framework can improve a pretrained single-step MAPF policy in the random-32-32-20 setting.
- **Metric**: success_rate_improvement_vs_policy_baseline (higher is better)
- **Metric**: normalized_solution_cost_factor_vs_policy_baseline (lower is better)
- **How to run**: evaluate the same pretrained policy and collision-shielded baseline on random-32-32-20, using the paper's real-time execution protocol.
# Targets

Optimize `success_rate` first on `scaled_small_mapf`. A valid improvement must
also preserve `valid_rate` and should not inflate `mean_expansions` by simply
doing much more search.

Every submitted method should write path artifacts that `scripts/evaluate.sh`
can score. The primary comparison is against `rt_lacam`, `full_lacam`, and
`naive_rt_lacam` in `scoring/scores.json`.
