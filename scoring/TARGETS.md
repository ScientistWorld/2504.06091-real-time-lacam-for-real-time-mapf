# Targets

Every experiment below appears in `scoring/scores_train.json` and
`scoring/scores_test.json` with the same four metrics.

| experiment | primary | reference `rt_lacam` (held-out) | frozen rows (held-out): full-horizon / restart |
|---|---|---|---|
| `scaled_small_mapf` | `realtime_score` | 0.508 (success 0.80) | 0.756 (0.80) / 0.125 (0.125) |
| `scaled_small_mapf_budget3` | `realtime_score` | 0.548 (success 0.80) | 0.747 (0.80) / 0.243 (0.25) |
| `movingai_random32` | `realtime_score` | 0.724 (success 0.75) | 0.747 (0.75) / 0.673 (0.6875) |

Benefit metrics: `realtime_score` (primary) and `success_rate`, higher is
better, in [0, 1]. Neither is at its bound for the reference.

Constraint metrics, lower is better:

- `mean_log_normalized_cost`: executed solution quality, including waits
  caused by overrunning the per-tick budget.
- `mean_log_planning_work`: total metered planning work per episode. The
  paper's claim is parity with full-horizon planning (reference 2.13 / 2.13 /
  2.06 vs full-horizon 2.07 / 2.07 / 1.97).

Hard constraints, enforced by the evaluator (a violation fails the instance):
legal moves only, the per-tick budget (overruns become waiting ticks), the
cumulative work cap, the tick horizon, and no tampering with the meter.

Train-slice values of the reference are 0.614 / 0.664 / 0.595 (success 0.85 /
0.85 / 0.625). The train and test slices are disjoint samples from the same
generators, so per-experiment values differ by sampling, in both directions.
