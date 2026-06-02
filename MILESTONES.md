# Reproduction Milestones

**Current: core_claim**

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

## Stop Justification
- Not stopped; a CPU compute job is being submitted to verify the packaged
  environment end to end.
