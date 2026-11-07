# Constraints

- A method is a planner registered in `outputs/planners/` that implements the
  interface in `briefing/evaluation.md`. The evaluators run it themselves; the
  instances, per-tick budgets, cumulative work caps, tick horizons, comparison
  rows and test size are fixed by `eval/` and cannot be changed by a method.
- All planning computation must happen inside the metered calls
  (`make_planner` and `step`) as ordinary Python. Do not move planning work out
  of the meter's reach: no C extensions or native libraries doing the search,
  no subprocesses, no threads that outlive a call, no disabling or
  manipulating the trace hook, and no reading of evaluator internals (frames,
  meter state, the result file, or the held-out evaluator's source). The
  evaluator detects the common forms and fails the instance; the rest count as
  shortcuts.
- Do not precompute plans for specific instances. Train-slice instances are
  visible, and replaying cached train plans inflates train scores only.
- Every returned move must be a legal one-tick move. Teleports, collisions and
  swaps fail the instance.
- Wall-clock time is never measured. Planning effort is the metered event
  count, and over-budget decisions cost waiting ticks.
- Keep the real-time setting: the planner may plan as much as it likes, but
  every tick it is late, the agents wait and the path gets more expensive.
