# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

### [2026-06-02 15:51] - core_claim
- Implemented Real-Time LaCAM with persistent lazy DFS, constrained successor generation, first-action execution, and re-rooting.
- Scored a scaled MAPF benchmark showing Real-Time LaCAM matches full-horizon LaCAM success while naive restart replanning fails on some instances.

### [2026-06-02 16:07] - core_claim_plus
- Replaced the simplified one-step generator with constrained PIBT-style recursive priority inheritance and backtracking.
- Verified both one-expansion and three-expansion real-time budgets locally with `bash scripts/reproduce.sh` and `python validate.py --compare`.

## Stop Justification
- Not stopped; submitting a container verification job for the patched implementation.
