# Overview

Real-Time LaCAM addresses real-time MAPF, where agents must move after a tiny
planning budget instead of waiting for a full-horizon plan. The key idea is to
keep LaCAM's lazy DFS tree alive across execution steps and re-root that tree
after each executed move, which keeps the search complete.

The gym runs every registered planner online inside the evaluator, which meters
planning work, charges overrun decisions as waiting time, and scores the
executed paths. It compares the paper's planner with two evaluator-owned rows,
a full-horizon planner that plans once and a real-time planner that restarts
its search every tick, on small congested grids at two per-tick budgets and on
the MovingAI random-32-32-20 map.

On the held-out slice the reproduction shows the paper's claim. The real-time
planner solves exactly as many instances as the full-horizon planner in every
experiment (success 0.80 / 0.80 / 0.75), with comparable total planning work,
whereas restart replanning collapses on the congested grids (0.125 / 0.25) and
trails on random-32-32-20 (0.69). Tight budgets cost solution quality, the
weakness the paper reports, which leaves clear headroom: realtime_score is
0.51 / 0.55 / 0.72, well below the bound of 1.

---

# Problem

Multi-Agent Path Finding (MAPF) asks for collision-free paths for several
agents on a shared 4-connected grid. Every agent starts at a cell and has a
goal cell; at every timestep each agent moves to an adjacent free cell or waits.
A joint move is legal only if no two agents end in the same cell (vertex
collision) and no two agents swap cells (edge collision).

This gym studies **real-time** MAPF. The planner is not given time to compute a
complete plan before the agents start. Instead, planning and execution
interleave: at every tick the planner receives the current joint configuration
and must return the next joint configuration within a small, fixed planning
budget. The agents execute that move, and the loop repeats until every agent
stands on its goal. A planner that needs more than one tick's budget for a
decision is late: the agents wait in place for the ticks it overran.

What makes the problem hard:

- In congested settings (narrow corridors, crossings, dense obstacle fields)
  greedy one-step decisions deadlock or livelock, so a real-time planner must
  still make global progress although it only ever commits to one move.
- Tight per-tick budgets trade against solution quality: myopic moves can make
  the executed paths far longer than necessary.
- The total planning effort across the whole episode should stay comparable
  to that of planning the full horizon once.

Success therefore means: legal execution, reaching all goals within the
episode's limits, a short executed sum of costs, and modest total planning
work.

The benchmark consists of small congested grids (corridors with passing
pockets, four-way crossings, dense random grids with 5-7 agents) and the
MovingAI MAPF benchmark map random-32-32-20 with 6-12 agents. These are scaled
down from published benchmark sizes so that pure-Python planners can be
evaluated quickly; the coordination problem stays the same.

---

# Method

The paper proposes Real-Time LaCAM, an incremental version of LaCAM for
real-time MAPF.

LaCAM performs a lazy depth-first search over joint configurations. Instead of
enumerating all joint moves at once, each configuration generates one successor
at a time using a fast one-step MAPF generator. When a configuration is
revisited, additional action constraints force the generator to explore a new
successor (first constraining one agent's action, then two agents', and so
on). In the limit, the constrained generator covers the same joint action
space as exhaustive DFS, which makes the search complete.

Real-Time LaCAM keeps the DFS state across planning and execution iterations.
At each iteration it continues the existing DFS until the per-iteration
cutoff, recovers the path from the DFS cursor back to the current executed
configuration, and executes the first joint action on that path. After
execution it re-roots the DFS tree at the new current configuration by
reversing the executed tree edge. Because it builds the same search tree as
full-horizon LaCAM, it keeps LaCAM's completeness and total planning effort.

The packaged implementation (`method/rt_lacam.py`) implements this structure:
lazy joint-configuration DFS split into single constrained-generator attempts,
the LaCAM constraint schedule, persistent search state, and re-rooting. The
per-iteration cutoff is read from the evaluator's work clock. The one-step
generator is a deterministic PIBT-style recursive priority-inheritance planner
that honours a forced prefix of agent actions. It is weaker than the PIBT used
in the paper: when greedy one-step planning stalls, the lazy constraint search
can need very many attempts, which limits the agent counts the packaged
planner solves.

---

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
| `scaled_small_mapf` | 40 small congested grids (10 corridors, 8 crossings, 22 dense) | 1,000 | 2,000,000 |
| `scaled_small_mapf_budget3` | the same 40 grids | 3,000 | 2,000,000 |
| `movingai_random32` | 32 random-32-32-20 instances, 8 each with 6/8/10/12 agents | 3,000 | 6,000,000 |

The train slice and the held-out test slice use the same generators and
operating points with different seeds. They are disjoint by construction: an
instance belongs to one slice according to a hash of its
agent-order-invariant form, and duplicates within a slice are rejected. The
test instances exist only inside the held-out evaluator.

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

---

# Reproduction Log

### Iteration 1: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 14m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 15:45] - none
- Read the paper markdown and identified the central claim: persistent
  Real-Time LaCAM should match full-horizon LaCAM success under small
  per-iteration planning budgets, unlike naive restart replanning.

### [2026-06-02 16:05] - method_runs
- Implemented lazy joint-configuration DFS, constrained successor generation,
  persistent Real-Time LaCAM state, and tree re-rooting.
- Added deterministic scaled MAPF benchmark instances and runnable method,
  baseline, and evaluation scripts.

### [2026-06-02 16:15] - core_claim
- Ran `bash scripts/reproduce.sh` locally as a smoke test.
- Real-Time LaCAM solved all 6 scaled instances with valid paths.
- Full-horizon LaCAM also solved all 6 instances; both used mean expansions
  14.5, matching the paper's search-effort parity claim at this scale.
- Naive real-time restart LaCAM solved 4 of 6 instances, demonstrating the
  failure mode addressed by persistent search state.

### [2026-06-02 16:48] - core_claim
- Compute job `c3151de9-ae4` exited 0 and passed `python validate.py --compare`
  inside the container.
- Added a second per-iteration expansion setting locally; this is ready for a
  follow-up CPU job before claiming `core_claim_plus`.

### [2026-06-02 16:52] - core_claim_plus
- Compute job `1ac94747-97f` exited 0 and passed `python validate.py --compare`
  inside the container.
- Verified the core Real-Time LaCAM success-parity claim at two per-iteration
  expansion settings: 1 expansion and 3 expansions.
- In both settings, Real-Time LaCAM solved all 6 scaled instances with valid
  paths and matched full-horizon LaCAM's mean expansion count of 14.5.

</details>

### Iteration 2: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 3 total (3 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 15:51] - core_claim
- Implemented Real-Time LaCAM with persistent lazy DFS, constrained successor generation, first-action execution, and re-rooting.
- Scored a scaled MAPF benchmark showing Real-Time LaCAM matches full-horizon LaCAM success while naive restart replanning fails on some instances.

### [2026-06-02 16:07] - core_claim_plus
- Replaced the simplified one-step generator with constrained PIBT-style recursive priority inheritance and backtracking.
- Verified both one-expansion and three-expansion real-time budgets locally with `bash scripts/reproduce.sh` and `python validate.py --compare`.

### [2026-06-02 16:18] - core_claim_plus
- Audited the continued workspace against implementation, evaluation, and deliverable requirements.
- Fixed the LaCAM lazy constraint schedule so attempts use block-local enumeration: 5 constraints for one agent, then 5^2 for two agents, continuing through all forced-prefix blocks.
- Re-ran the scaled reproduction locally; Real-Time LaCAM still matches full-horizon success on both per-iteration budgets and validation passes.

### [2026-06-02 16:25] - core_claim_plus
- Container verification job `3bc2147c-29f` exited 0.
- The job ran `scripts/run.sh`, regenerated both scaled experiments, and passed `python validate.py --compare` inside the compute container.
- Final milestone remains `core_claim_plus`: the core claim is reproduced on the minimum one-expansion setting and an additional three-expansion setting.

</details>

### Iteration 3: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 8m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 15:57] - core_claim
- Implemented Real-Time LaCAM with persistent lazy DFS, constrained one-step successor generation, and tree re-rooting.
- Verified the scaled benchmark core claim: Real-Time LaCAM matched full-horizon LaCAM success while naive restart replanning failed on congested cases.

### [2026-06-02 16:00] - core_claim_plus
- Added a public MovingAI MAPF random-32-32-20 four-agent subset and self-contained download script.
- Verified an additional benchmark-backed setting in compute job `96b00c84-d41`: Real-Time LaCAM and full-horizon LaCAM solved all three MovingAI instances, while naive restart replanning solved two of three.
- Fixed the audit issue where `valid_rate` incorrectly required reaching the goal; it now measures legal/collision-free execution separately from `success_rate`.

</details>

### Iteration 4: gpt-5.5 (designer_stage_1)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 4m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 15:57] - core_claim
- Implemented Real-Time LaCAM with persistent lazy DFS, constrained one-step successor generation, and tree re-rooting.
- Verified the scaled benchmark core claim: Real-Time LaCAM matched full-horizon LaCAM success while naive restart replanning failed on congested cases.

### [2026-06-02 16:00] - core_claim_plus
- Added a public MovingAI MAPF random-32-32-20 four-agent subset and self-contained download script.
- Verified an additional benchmark-backed setting in compute job `96b00c84-d41`: Real-Time LaCAM and full-horizon LaCAM solved all three MovingAI instances, while naive restart replanning solved two of three.
- Fixed the audit issue where `valid_rate` incorrectly required reaching the goal; it now measures legal/collision-free execution separately from `success_rate`.

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 15:57] - core_claim
- Implemented Real-Time LaCAM with persistent lazy DFS, constrained one-step successor generation, and tree re-rooting.
- Verified the scaled benchmark core claim: Real-Time LaCAM matched full-horizon LaCAM success while naive restart replanning failed on congested cases.

### [2026-06-02 16:00] - core_claim_plus
- Added a public MovingAI MAPF random-32-32-20 four-agent subset and self-contained download script.
- Verified an additional benchmark-backed setting in compute job `96b00c84-d41`: Real-Time LaCAM and full-horizon LaCAM solved all three MovingAI instances, while naive restart replanning solved two of three.
- Fixed the audit issue where `valid_rate` incorrectly required reaching the goal; it now measures legal/collision-free execution separately from `success_rate`.

</details>

### Iteration 6: gpt-5.5 (designer_stage_3)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 6 total (6 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 15:57] - core_claim
- Implemented Real-Time LaCAM with persistent lazy DFS, constrained one-step successor generation, and tree re-rooting.
- Verified the scaled benchmark core claim: Real-Time LaCAM matched full-horizon LaCAM success while naive restart replanning failed on congested cases.

### [2026-06-02 16:00] - core_claim_plus
- Added a public MovingAI MAPF random-32-32-20 four-agent subset and self-contained download script.
- Verified an additional benchmark-backed setting in compute job `96b00c84-d41`: Real-Time LaCAM and full-horizon LaCAM solved all three MovingAI instances, while naive restart replanning solved two of three.
- Fixed the audit issue where `valid_rate` incorrectly required reaching the goal; it now measures legal/collision-free execution separately from `success_rate`.

</details>

### Iteration 7: gpt-5.5 (packager)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 2m | **GPU**: 0.0h
- **Jobs**: 6 total (6 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 15:57] - core_claim
- Implemented Real-Time LaCAM with persistent lazy DFS, constrained one-step successor generation, and tree re-rooting.
- Verified the scaled benchmark core claim: Real-Time LaCAM matched full-horizon LaCAM success while naive restart replanning failed on congested cases.

### [2026-06-02 16:00] - core_claim_plus
- Added a public MovingAI MAPF random-32-32-20 four-agent subset and self-contained download script.
- Verified an additional benchmark-backed setting in compute job `96b00c84-d41`: Real-Time LaCAM and full-horizon LaCAM solved all three MovingAI instances, while naive restart replanning solved two of three.
- Fixed the audit issue where `valid_rate` incorrectly required reaching the goal; it now measures legal/collision-free execution separately from `success_rate`.

</details>

### Iteration 8: gpt-5.5 (verifier)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 6 total (6 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 15:57] - core_claim
- Implemented Real-Time LaCAM with persistent lazy DFS, constrained one-step successor generation, and tree re-rooting.
- Verified the scaled benchmark core claim: Real-Time LaCAM matched full-horizon LaCAM success while naive restart replanning failed on congested cases.

### [2026-06-02 16:00] - core_claim_plus
- Added a public MovingAI MAPF random-32-32-20 four-agent subset and self-contained download script.
- Verified an additional benchmark-backed setting in compute job `96b00c84-d41`: Real-Time LaCAM and full-horizon LaCAM solved all three MovingAI instances, while naive restart replanning solved two of three.
- Fixed the audit issue where `valid_rate` incorrectly required reaching the goal; it now measures legal/collision-free execution separately from `success_rate`.

</details>

### Iteration 9: gpt-5.5 (verifier)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 6 total (6 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 15:57] - core_claim
- Implemented Real-Time LaCAM with persistent lazy DFS, constrained one-step successor generation, and tree re-rooting.
- Verified the scaled benchmark core claim: Real-Time LaCAM matched full-horizon LaCAM success while naive restart replanning failed on congested cases.

### [2026-06-02 16:00] - core_claim_plus
- Added a public MovingAI MAPF random-32-32-20 four-agent subset and self-contained download script.
- Verified an additional benchmark-backed setting in compute job `96b00c84-d41`: Real-Time LaCAM and full-horizon LaCAM solved all three MovingAI instances, while naive restart replanning solved two of three.
- Fixed the audit issue where `valid_rate` incorrectly required reaching the goal; it now measures legal/collision-free execution separately from `success_rate`.

</details>

### Iteration 10: gpt-6.1-sol (redteam)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 10m | **GPU**: 0.0h
- **Jobs**: 6 total (6 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 15:57] - core_claim
- Implemented Real-Time LaCAM with persistent lazy DFS, constrained one-step successor generation, and tree re-rooting.
- Verified the scaled benchmark core claim: Real-Time LaCAM matched full-horizon LaCAM success while naive restart replanning failed on congested cases.

### [2026-06-02 16:00] - core_claim_plus
- Added a public MovingAI MAPF random-32-32-20 four-agent subset and self-contained download script.
- Verified an additional benchmark-backed setting in compute job `96b00c84-d41`: Real-Time LaCAM and full-horizon LaCAM solved all three MovingAI instances, while naive restart replanning solved two of three.
- Fixed the audit issue where `valid_rate` incorrectly required reaching the goal; it now measures legal/collision-free execution separately from `success_rate`.

</details>


---

# Reproduction Milestones

**Current: core_claim_plus**

## Stop Justification
- Completed at milestone `core_claim_plus`.
