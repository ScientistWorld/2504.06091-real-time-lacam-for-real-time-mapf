# Overview

Real-Time LaCAM addresses real-time MAPF, where agents must execute after a
tiny planning budget rather than wait for a full-horizon plan. The key idea is
to keep LaCAM's lazy DFS tree alive across execution steps and re-root that
tree after each executed move.

The packaged reproduction compares full-horizon LaCAM, Real-Time LaCAM, and a
naive real-time restart baseline on scaled congested MAPF instances and a small
public MovingAI subset. The current results demonstrate the core claim:
Real-Time LaCAM matches full-horizon success on all packaged settings while
the naive restart baseline fails on some instances.

---

# Problem

Multi-Agent Path Finding (MAPF) asks for collision-free paths for multiple
agents moving on a shared grid. Each agent starts at a cell, has a goal cell,
and may move one cardinal step or wait at each timestep. A valid solution must
avoid vertex collisions and edge-swap collisions.

This reproduction focuses on real-time MAPF. The solver receives a small
planning budget, outputs the next joint action, executes that action, and then
replans from the new joint configuration until all agents reach their goals.

Success requires:

- Valid executed paths with no illegal moves or collisions.
- High episode success under bounded per-iteration planning.
- A cumulative search effort comparable to full-horizon planning.
- Nontrivial coordination in congested instances where naive restart replanning
  can deadlock or livelock.

The benchmark uses deterministic scaled-down grid instances with narrow
passages, cross traffic, and random dense maps, plus a small public MovingAI
random-32-32-20 subset. The scale differs from the paper's largest benchmark
scenes so the environment can run quickly, but the problem remains MAPF
coordination under congestion.

---

# Method

The paper proposes Real-Time LaCAM, an incremental version of LaCAM for
real-time MAPF.

LaCAM performs a lazy depth-first search over joint configurations. Instead of
enumerating all joint moves at once, each configuration generates one successor
at a time using a fast one-step MAPF generator. When a configuration is
revisited, additional action constraints force the generator to explore a new
successor. In the limit, the constrained generator covers the same joint action
space as exhaustive DFS.

Real-Time LaCAM keeps the DFS state across planning and execution iterations.
At each iteration it continues the existing DFS for a small budget, recovers the
path from the DFS cursor back to the current executed configuration, and
executes the first joint action on that path. After execution it re-roots the
DFS tree at the new current configuration by reversing the executed tree edge.

This reproduction implements the paper's computational structure: lazy
joint-configuration DFS, constrained successor generation, persistent search
state, and re-rooting. The one-step generator is a deterministic constrained
PIBT-style recursive priority-inheritance planner; fully constrained attempts
enumerate valid joint actions, preserving the lazy constrained search behavior
needed by LaCAM.

---

# Evaluation

`scripts/evaluate.sh` reads solver artifacts from `outputs/*.json` and invokes
only code in `eval/` plus problem utilities in `data/`. It does not import
`method/`, so future agents can replace the method as long as they emit the
same artifact format.

Each artifact contains a list of explicit joint-configuration paths. The
evaluator independently checks path validity and computes:

- `success_rate`: fraction of instances ending at all goals with a valid path.
- `valid_rate`: fraction of instances with legal moves and no collisions.
- `mean_normalized_cost`: mean sum-of-costs divided by the sum of individual
  shortest path lengths, over solved instances.
- `mean_expansions`: mean generated-successor expansion count, used as a
  hardware-independent search effort constraint.
- `instances`: number of benchmark instances scored.

The core claim is supported when Real-Time LaCAM matches full-horizon LaCAM on
success while using bounded per-iteration expansions, and the naive real-time
restart baseline has lower success on the same instances.

The packaged score file includes two scaled deterministic settings and one
public MovingAI random-32-32-20 four-agent setting.

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


---

# Reproduction Milestones

**Current: core_claim_plus**

## Stop Justification
- Completed at milestone `core_claim_plus`.
