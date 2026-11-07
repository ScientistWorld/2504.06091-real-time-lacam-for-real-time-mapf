# Design Notes

> Superseded: this note describes the artifact-based evaluator replaced in
> iteration 11. See HARDENING.md and briefing/evaluation.md for the current gym.


## Checks Performed

- Reviewed `scripts/evaluate_train.sh` and `scripts/evaluate_test.sh` side by side. The train script calls `eval/train/evaluate.py` and writes `scoring/scores_train.json`; the test script calls `eval/test/evaluate.py`, marks the output as the held-out slice through the evaluator, and writes `scoring/scores_test.json`.
- Reviewed `eval/train/evaluate.py` and `eval/test/evaluate.py` for method detachment. Both evaluators rescore JSON artifacts emitted by methods rather than importing or rerunning `method/`.
- Checked train/test leakage with grep. The only train/test references are script entry points and explanatory docstrings; there are no cross-imports between the two evaluator folders.
- Checked `scoring/reference.json` for paper-agreement metrics. No metric is shaped like deviation from paper-reported values.
- Confirmed `scoring/scores_train.json` and `scoring/scores_test.json` do not exist.
- Ran static-only validation: `bash -n` on both train/test scripts and JSON parsing for `scoring/reference.json`.

## Changes Made

- Fixed a selective-omission shortcut in both evaluators. Previously, success and validity were averaged only over artifact rows that existed, so a method could omit hard instances and still score well. Missing expected instances now count as unsuccessful and invalid.
- Added `coverage_rate` to both train and test evaluator outputs. This exposes whether an artifact covered every expected slice instance.
- Added `duplicate_results` to both train and test evaluator outputs. This penalizes padding artifacts with repeated rows for the same expected instance.
- Changed the `instances` field emitted by train/test evaluators to report the expected slice size, not the number of rows a method happened to emit.
- Updated `scoring/reference.json` with `coverage_rate` and `duplicate_results` for all existing experiments.
- Added the required `description` field to every metric entry in `scoring/reference.json`.

## Runtime Concerns For Next Iteration

- The MovingAI held-out test slice has only one scenario while train has two. This is useful as a hidden domain check but is statistically small; the runner should watch for noisy pass/fail behavior if future outputs vary across scenarios.
- `mean_expansions` is averaged over represented instances only. Missing instances are already penalized through `success_rate`, `valid_rate`, and `coverage_rate`, but the runner should confirm this weighting does not let low-coverage methods benefit from artificially low expansion counts.
- The train/test evaluators intentionally duplicate logic instead of sharing a helper to avoid leakage. Future edits should keep both copies synchronized.
