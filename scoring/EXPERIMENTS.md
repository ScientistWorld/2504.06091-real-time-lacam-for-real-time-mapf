# Experiments

All three experiments run every registered planner online inside the
evaluator, with the evaluator metering planning work and executing every move.
Each reports the same four metrics (see `briefing/evaluation.md`): the primary
`realtime_score`, `success_rate`, `mean_log_normalized_cost` and
`mean_log_planning_work`. Each also reports two evaluator-owned comparison
rows: a full-horizon planner that plans once offline, and a real-time planner
that restarts its search every tick.

**`scaled_small_mapf`** (weight 0.34): small congested grids (single-file
corridors with a few passing pockets, four-way crossings, dense random grids)
at the tightest per-tick planning budget. It tests the central claim: a
real-time planner that only commits one move per tick can still finish the
congested instances that a full-horizon planner finishes, whereas restarting
the search every tick deadlocks or livelocks. It also shows how much solution
quality the tight budget costs.

**`scaled_small_mapf_budget3`** (weight 0.33): the same instances with a
three-times larger per-tick budget and the same cumulative work cap. It checks
that success parity is not an artifact of one cutoff, and that solution
quality improves as the cutoff grows.

**`movingai_random32`** (weight 0.33): the public MovingAI benchmark map
random-32-32-20 with 6-12 agents at random free cells. It repeats the
comparison on a standard benchmark map from the paper's evaluation at reduced
agent counts.

What a better method should show: more instances solved under the same budgets
and caps, shorter executed paths (including any waiting caused by overrunning
a tick), and no more total planning work. What the constraint side guards:
legality of every move, the per-tick budget (overruns become waiting), the
cumulative work cap, and the tick horizon. A failed instance scores the worst
value on every metric.
