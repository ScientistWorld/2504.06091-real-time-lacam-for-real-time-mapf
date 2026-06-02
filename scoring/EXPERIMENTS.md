# Experiments

`scaled_small_mapf` evaluates whether a real-time MAPF solver can solve
congested instances under tiny per-iteration planning budgets. It compares a
persistent real-time solver, a full-horizon solver, and a restart-from-scratch
real-time baseline.

The experiment measures both the benefit side of the claim (`success_rate`) and
the constraints that make the claim meaningful (`valid_rate`,
`mean_normalized_cost`, and `mean_expansions`).
