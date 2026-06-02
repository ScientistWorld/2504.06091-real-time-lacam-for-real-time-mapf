# Experiments

`scaled_small_mapf` evaluates whether a real-time MAPF solver can solve
congested instances under tiny per-iteration planning budgets. It compares a
persistent real-time solver, a full-horizon solver, and a restart-from-scratch
real-time baseline.

`scaled_small_mapf_budget3` repeats the same comparison with a larger
per-iteration expansion budget. It checks that the central success-parity claim
is not an artifact of a single cutoff setting.

`movingai_random32_4agent` evaluates the same claim on a small subset of the
public MovingAI MAPF benchmark, using random-32-32-20 random scenarios with
four agents. This adds a benchmark-backed setting closer to the paper's Figure
2 setup while keeping the reproduction lightweight.

The experiment measures both the benefit side of the claim (`success_rate`) and
the constraints that make the claim meaningful (`valid_rate`,
`mean_normalized_cost`, and `mean_expansions`).
