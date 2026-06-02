# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-06-02 15:57] - core_claim
- Implemented Real-Time LaCAM with persistent lazy DFS, constrained one-step successor generation, and tree re-rooting.
- Verified the scaled benchmark core claim: Real-Time LaCAM matched full-horizon LaCAM success while naive restart replanning failed on congested cases.

### [2026-06-02 16:00] - core_claim_plus
- Added a public MovingAI MAPF random-32-32-20 four-agent subset and self-contained download script.
- Locally smoke-tested an additional benchmark-backed setting: Real-Time LaCAM and full-horizon LaCAM solved all three MovingAI instances, while naive restart replanning solved two of three.
- Pending compute-job verification before claiming this milestone.

## Stop Justification
- Completed at milestone `core_claim`; `core_claim_plus` verification job is pending.
