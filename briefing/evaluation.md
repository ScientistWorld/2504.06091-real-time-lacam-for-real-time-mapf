# Evaluation

The evaluators (`eval/train/evaluate.py`, visible; and the held-out test
evaluator) **run your planner themselves**. They build the instances, drive the
real-time loop, meter planning work, execute and check every move, and score
the joint path they recorded. Nothing a planner writes to disk or reports is
trusted. `eval/` never imports `method/`.

## Registering a planner

Write a manifest `outputs/planners/<name>.json`:

```json
{"name": "my_planner", "entry": "method/my_planner.py", "factory": "make_planner"}
```

Every manifest in `outputs/planners/` is scored (`scripts/method.sh`
registers the packaged planner `rt_lacam`). The names `full_lacam`,
`naive_rt_lacam` and names starting with `_` are reserved for the evaluator's
comparison rows and are ignored.

## Planner interface

```python
def make_planner(instance: dict) -> Planner: ...

class Planner:
    def step(self, config, clock):  # -> next joint configuration
        ...
```

`instance` contains:

| key | content |
|---|---|
| `width`, `height` | grid size |
| `obstacles` | frozenset of blocked `(x, y)` cells |
| `starts`, `goals` | tuples of `(x, y)`, one per agent |
| `neighbors` | dict: free cell -> tuple of cells reachable in one tick (the cell itself first) |
| `dist` | tuple, one dict per agent: free cell -> shortest-path distance to that agent's goal |

`config` is a tuple of `(x, y)` cells, one per agent. `step` must return a
built-in `list`/`tuple` of N `(x, y)` pairs of `int` (no subclasses or lazy
objects). `clock.remaining()` returns the metered work left in the current
tick (negative once the tick's budget is overrun); `clock.budget` is the
per-tick budget.

## Metering and the real-time loop

- **Work unit.** Every executed Python line and every Python function call
  inside planner code (including standard-library Python code it calls)
  counts one event. The count is deterministic and hardware-independent; no
  wall-clock time is used anywhere in scoring.
- **Ticks.** A decision that costs W events occupies `ceil(W / B)` ticks for a
  per-tick budget B (at least one). During the first `ceil(W / B) - 1` of them
  every agent waits in place, and those waits are part of the executed path
  and its cost. `make_planner` is charged to the first decision.
- **Limits.** Each episode has a cumulative work cap and a tick horizon of
  `2 * cap / B` ticks. A decision that would cross either limit is interrupted
  and the episode fails.
- **Failure.** An episode fails on an illegal or malformed move, an exception,
  exhausting the work cap or the horizon, or tampering with the meter (tracing
  switched off, threads left running). Importing the planner module is metered
  separately (at most 200,000 events, not charged to any tick).
- Every episode runs in a fresh Python process; no state carries over between
  instances.

## Experiments and operating points

| experiment | instances | budget B per tick | cumulative work cap |
|---|---|---|---|
| `scaled_small_mapf` | 20 small congested grids | 1,000 | 2,000,000 |
| `scaled_small_mapf_budget3` | the same 20 grids | 3,000 | 2,000,000 |
| `movingai_random32` | 16 random-32-32-20 instances, 6-12 agents | 3,000 | 6,000,000 |

The train slice and the held-out test slice use the same generators and
operating points with different instances; the test instances exist only
inside the held-out evaluator.

## Metrics (per experiment, means over instances)

- `realtime_score` (primary, higher is better, in [0, 1]): 0 for a failed
  episode, otherwise `1 - log10(C / LB) / log10(C_max / LB)`, where C is the
  executed sum of costs (unit cost per agent per tick except an agent staying
  on its goal), LB the sum of the agents' individual shortest-path lengths,
  and C_max = agents x horizon the largest cost an execution inside the
  horizon can have.
- `success_rate` (higher is better): fraction of episodes that reach all goals
  legally within the limits.
- `mean_log_normalized_cost` (lower is better): mean `log10(C / LB)`; failed
  episodes count as `log10(C_max / LB)`.
- `mean_log_planning_work` (lower is better): mean `log10(1 + W_total / 1000)`
  over the whole episode; failed episodes count as the work cap.

## Comparison rows

Each score file also contains two rows the evaluator computes with its own
frozen planners under the same meter: `full_lacam`, a full-horizon search
that plans once offline and then executes its plan (not a real-time method;
its cost has no waits), and `naive_rt_lacam`, a real-time planner that
restarts its search from scratch every tick.

## Commands

```bash
bash scripts/method.sh          # register rt_lacam
bash scripts/evaluate_train.sh  # -> scoring/scores_train.json (train slice)
bash scripts/evaluate.sh        # same evaluator -> scoring/scores.json
bash scripts/evaluate_test.sh   # held-out slice -> scoring/scores_test.json (no arguments)
python3 eval/train/evaluate.py --details tmp/train_details.json   # per-instance train records
```
