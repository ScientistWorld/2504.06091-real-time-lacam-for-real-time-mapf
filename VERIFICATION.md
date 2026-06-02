# Verification Report

## Initial Assessment

The workspace claimed `core_claim_plus` and had a working Real-Time MAPF
reproduction with method, baseline, reusable evaluation, train/test slices,
MovingAI download support, and successful prior validation. The claimed
milestone is justified: the implementation visibly runs the paper's actual
incremental real-time MAPF search procedure at reduced scale, and the scored
results support the central success-parity claim on deterministic scaled
instances plus a small public MovingAI subset.

## Issues Found

- Minor: `briefing/evaluation.md` named the paper method and described the core
  comparison in solution-specific terms, which leaked method information into a
  strict method-agnostic file.
- Minor: `scoring/EXPERIMENTS.md` described one compared solver as
  "persistent", which was more implementation-specific than needed for a
  from-scratch scientist.
- Minor: `scoring/DIRECTION.md` explicitly named a method family. The allowed
  direction should stay at the problem-space level: bounded real-time MAPF and
  incremental/windowed search.
- Minor: `briefing/evaluation.md` said `mean_normalized_cost` was averaged over
  solved instances, but the evaluator also assigns deterministic penalties for
  failures, invalid paths, and omitted instances.
- Minor: `scoring/reference.json` uses scaled reproduction targets because the
  paper reports Figure 2 graphically/qualitatively rather than in an exact
  table. This needed explicit notes.

## Fixes Applied

- Reworded `briefing/evaluation.md` to describe bounded real-time solvers,
  full-horizon comparators, restart baselines, and failure-penalized normalized
  cost without naming the paper method.
- Reworded `scoring/EXPERIMENTS.md` and `scoring/DIRECTION.md` to avoid leaking
  implementation strategy while preserving the intended real-time MAPF research
  direction.
- Added `notes` fields to all `scoring/reference.json` experiments explaining
  that the values are scaled reproduction targets for the paper's qualitative
  graphical claim.
- Made `scoring/reference.json` experiment descriptions method-neutral.
- Re-ran `bash scripts/evaluate.sh` and `python validate.py --compare`; all
  checks passed.

## Final Judgment

The workspace is ready to serve as a research gym. The strict method-agnostic
files now describe the task and evaluation without revealing the paper's
algorithm. `eval/` and `data/` do not import `method/`, `scripts/evaluate.sh`
scores output artifacts rather than rerunning the method, train/test slices are
present and independent, and the download script uses verified public MovingAI
URLs without `shared/` references.

- Milestone: core_claim_plus
- Ready for gym use: yes
- Confidence: high
- Key limitation: scaled benchmark and reduced MovingAI subset rather than the
  paper's full 25-scene-per-map benchmark.
