# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

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

## Stop Justification
- Completed at milestone `core_claim_plus`.
