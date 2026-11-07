# Scoring audit

Run `bash redteam/<case>/run.sh` on a compute node. `reference_seed0`
rebuilds the fixed comparison artifacts and the original method first; other
cases reuse that run's comparison artifacts. `python3 redteam/audit.py --all`
bundles the runs. The only required packages are the gym's standard library.

Each case installs its method or changes output artifacts at the canonical
paths, runs the visible train evaluator, and invokes
`bash scripts/evaluate_test.sh` **without arguments** in a separate process
after the generator exits. The evaluator is checked byte for byte against the
starting git revision. No process, Python import modification, special routing
environment variable, or evaluator modification is used. These are file-based
attempts that persist into a fresh evaluator process/container. The scheduler
runs the bundle in a fresh CPU compute container.

All method generators use only agent-visible sources: `method/` (quality
variants and the reference, improve mode), `baseline/`, `data/`, and method
outputs reproducibly obtained from those sources. In particular, the offline
cache shortcut derives plans from `baseline/lacam_core.py`, which is also
available in from-scratch mode. It never reads hidden test code, scores, or
instance lists. Reference output reuse in other shortcuts avoids rerunning an
identical method. No paper is used.

Quality variants retain the original per-iteration expansion budgets,
cumulative budgets, and execution limits. They change agent priorities,
action tie breaking, or restore recursive reservations after failed branches.
All four are measured rather than assuming any improves quality. The
`weak_no_memory` variant actually reruns the supplied restart baseline;
`weak_limited_steps` executes the original method with one permitted action.

Each folder saves `scores_train.json`, `scores_test.json`, artifact JSONs,
command exit codes, and evaluator hashes. The harness backs up every changed
file outside `redteam/` before a case and restores it in `finally`. If a job
is killed, run `python3 redteam/audit.py --recover` before resuming. Completed
runs are skipped when the whole bundle is resumed.

The score files contain metric vectors, not an aggregate ranking. Any weighted
sum reported by this audit is explicitly a diagnostic using the declared
coefficients in `scoring/reference.json`, rather than an invented external
ranking function. Pareto improvements and ties do not require that assumption.

A second CPU bundle adds ten ordinary search-order policies (agent ID, initial
distance, coordinate tie breaking, goal traffic, constraint order, rotations,
and heading continuity) and a shortcut that edits the train-score manifest
between the visible and hidden runs. All policies are reported, including
unsuccessful ones; there is no hidden-test selection presented as a held-out
scientific result. A single-case `run.sh` reruns the case; `--all` skips completed
cases to resume a bundle.
