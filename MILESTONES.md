# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

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

## Stop Justification
- Completed at milestone `core_claim_plus`.
