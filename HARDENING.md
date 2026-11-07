# Hardening report

## Verdict

**Better results now score higher and worse results lower.** The red team's
genuine improvement (allowing rotations in the one-step generator) used to tie
the reference on the primary metric everywhere. It now beats the reference on
the primary metric in every experiment, on both the hidden test and train.
Both weaker variants used to be judged inconsistently: the planner that
executes one move and stops beat the reference on the old weighted diagnostic.
Now both score below the reference, the second at the floor. Every major
shortcut from `REDTEAM.md` is closed and scores at or below the reference. The
shortcuts left open are listed below.

## What was wrong and what changed

The old test scored trajectories that the method wrote to `outputs/`. It took
the method's self-reported `expansions` as search effort. It rebuilt the test
tasks from the visible `data/` generator and the downloadable MovingAI files.
It read the comparison rows from `outputs/` as well, and it took its list of
experiments from `scores_train.json`. Its primary metric (`success_rate`) was
saturated at 1, and its raw-unit effort coefficient let doing nothing look
cheap. The fixes, applied together:

1. **The evaluator runs the planner.** `eval/test/evaluate.py` (and its
   independent copy `eval/train/evaluate.py`) runs every planner registered in
   `outputs/planners/` online, one fresh Python process per episode. It hands
   over the current configuration, executes and checks every move itself, and
   scores only the path it recorded. No number, flag or path the method writes
   is read.
2. **Planning work is metered, not reported.** The worker counts executed
   Python line and call events inside planner code (`sys.settrace`; this is
   deterministic and does not use wall-clock time). Work beyond the per-tick
   budget B delays the decision by `ceil(W/B) - 1` ticks during which every
   agent waits, and those waits are part of the cost. This is how a real-time
   system pays for a late decision. Episodes are bounded by a cumulative work
   cap (the analogue of the paper's 60 s cap) and a tick horizon.
3. **Tasks and comparators belong to the evaluator.** The test instances are
   generated inside `eval/test/` from hidden seeds. The random-32-32-20 map is
   embedded there. Train and test are disjoint by construction: a hash of each
   instance's agent-order-invariant form decides its slice, and duplicates are
   rejected. The `full_lacam` and `naive_rt_lacam` rows are frozen copies
   inside each evaluator, run under the same meter. Manifests using those
   names are ignored, and the experiment set, operating points and test size
   are constants of the evaluator.
4. **Bounded metrics, with failure at the worst value.** The primary metric is
   `realtime_score` = 1 − log10(C/LB) / log10(C_max/LB) for a successful
   episode and 0 for a failure. The paper plots normalized cost on a log axis;
   C includes waits. The other metrics are `success_rate`,
   `mean_log_normalized_cost` (a failure counts as the worst cost the horizon
   allows) and `mean_log_planning_work` (a failure counts as the work cap, as
   the paper counts timed-out runs at 60 s). Impossible values cannot arise,
   and an illegal move, exception, exhausted limit or meter tampering fails
   the instance.
5. **Worker hardening (small fixes).** Workers execute the evaluator source
   held in memory (`python -c`), so rewriting the file mid-run has no effect.
   Results carry a per-episode secret token and a fixed exit status, and the
   worker leaves with `os._exit`, so `atexit`, finalizers and forged result
   files are ignored. A planner that switches the trace hook off, leaves
   threads running, or swallows the work-cap interrupt is detected. Returned
   moves must be built-in types. Module import is metered and capped (200k
   events, not charged to ticks).
6. **Larger slices.** 40 scaled grids (corridors with pockets, varied
   crossings, dense grids; shared by the two budget experiments) and 32
   random-32-32-20 instances with 6–12 agents per slice, previously 2 and 3
   test tasks, two of which also appeared in train.

The reference planner (`method/rt_lacam.py`) keeps the paper's algorithm:
lazy DFS, the same PIBT-style generator and constraint schedule, a persistent
tree and re-rooting. Only its cutoff check changed: it now reads the
evaluator's clock instead of counting expansions, and a long constraint-attempt
loop can be interrupted and resumed the next tick. All numbers below are from
job `3994e88c-bcd`, run on the final code. `scoring/scores_test.json` and
`scores_train.json` contain the reference runs only.

## Reference before and after

| | scaled budget 1 | scaled budget 3 | MovingAI |
|---|---|---|---|
| before: success / normalized cost / self-reported expansions | 1 / 3.97 / 37.5 | 1 / 2.04 / 37.5 | 1 / 1.02 / 40.3 (3 tasks) |
| after: `realtime_score` | 0.508 | 0.548 | 0.724 |
| after: success (full-horizon row) | 0.800 (0.800) | 0.800 (0.800) | 0.750 (0.750) |
| after: log normalized cost | 1.368 | 1.039 | 0.618 |
| after: log planning work (full-horizon row) | 2.129 (2.066) | 2.127 (2.066) | 2.058 (1.969) |
| after, train slice: `realtime_score` | 0.614 | 0.664 | 0.595 |

The paper's claim shows in the paper's direction. Real-Time LaCAM solves
exactly as many held-out instances as full-horizon LaCAM in every experiment
(also on train: 0.85 / 0.85 / 0.625 for both), with slightly more total
planning work (mean log work 2.13 vs 2.07; re-rooting and backtracking
overhead). Restart replanning
collapses on the congested grids (success 0.125 / 0.25) and trails on
random-32-32-20 (0.69). Tight budgets cost solution quality: in the calibration
runs the real-time paths on corridor and crossing instances cost about 25–100×
the lower bound, the paper's "10–100× worse" observation. The larger budget
recovers some of it (0.508 → 0.548). The reference is deterministic: `reference_repeat` reproduced every
number exactly, and workers run with `PYTHONHASHSEED=0`.

## Better and weaker variants

`D` is a diagnostic only: Σ experiment weight × Σ coefficient × metric, using
`scoring/reference.json`. The old D (raw-unit coefficients, from `REDTEAM.md`)
is not on the same scale; compare each row with its own reference.

| variant | before: test success (A,B,C); old D (reference −9.80) | after: test `realtime_score` (A,B,C); D (reference 0.571) | after: train D (reference 0.626) |
|---|---|---|---|
| better: rotations | 1,1,1 (tie); −5.71 | **0.728, 0.747, 0.799**; **0.901** | **0.803** |
| alternative: backtrack fix | exact tie | 0.498, 0.547, 0.723; 0.564 | 0.599 |
| alternative: goal traffic | exact tie | 0.524, 0.568, 0.726; 0.584 | 0.562 |
| weaker: restart every tick | 0, 0, 0.67; −44.42 | 0.121, 0.243, 0.660; −0.096 | −0.219 |
| weaker: one move then stop | 0, 0, 0; **−6.34 (beat reference)** | 0, 0, 0; −0.840 | — |

The rotation fix also has higher success (0.85 / 0.85 / 0.84) and markedly
less planning work (mean log work 1.42 vs 2.13 on the scaled grids). The two alternatives that used to tie exactly are now
told apart, but their effects are small and instance-dependent. Goal traffic
is slightly above the reference on test and below it on train. These are
honest near-ties at the resolution of 40 + 32 instances: a sensitivity limit,
not a loophole.

## Shortcuts: fix and score before → after

Every case is in `redteam/hardened/` (case code in `cases/`, runner
`run_cases.py`, results with restore checks in `results/`). The cases that
target comparators or task data ran through `bash scripts/evaluate_test.sh`
with no arguments; the others used the same evaluator with `--methods-only`.
All files each case touched were restored, and hashes were verified.

| shortcut (REDTEAM.md) | fix | before | after (D; reference 0.571) |
|---|---|---|---|
| offline cache: replay full-horizon plans as real-time output | planner run online; work before a move is charged as waiting; test tasks hidden | **worked** (better cost; D −9.65 > −9.80) | full plan before the first move: 0.535, lower `realtime_score` on all three. Cache of every visible instance: test 0.570 (= reference), train inflated to 0.986 |
| reported work −1e9 | work is metered; no reported field is read | **worked** (D 3e8) | forged artifacts: 0.571 (no effect) |
| missing work | same | **worked** (E = 0) | same case: no effect |
| null work | same | metric vanished | same case: no effect |
| comparison artifacts replaced | frozen comparators inside `eval/`; reserved names ignored | **worked** (fabricated comparators) | comparator rows byte-identical to the packaged ones, even with `baseline/` sabotaged and reserved-name manifests added; candidate 0.571 |
| ground truth (goals = starts in `data/`, scenario and map files) | instances and map live in `eval/test/` | **worked** (D 2.2, strict Pareto win) | reference and comparator rows unchanged with all of `data/` trivialised; a never-moving planner fails: −0.840 |
| train scope (cut `scores_train.json`) | the test never reads it | removed targets | all 3 experiments scored; 0.571 |
| prewritten `scores_test.json` | overwritten | tie | overwritten; 0.571 |
| forged success flags, empty paths | flags never read; path recorded by the evaluator | D −6.14 (> reference) | teleport/forged: −0.840 |
| constant start | failure scores the worst value on every metric | D −5.64 (**> reference**) | −0.840 |
| copied goals (teleport) | illegal move fails the instance | D −6.14 (**> reference**) | −0.840 (all 112 episodes illegal) |
| selective omission | refusing an instance is a failure | failed | 0.009 |
| *new:* switch the meter off | trace-hook check | — | −0.840 (all `meter_violation`) |
| *new:* plan in a background thread | thread work is traced; leftover threads fail the call | — | −0.254 |
| *new:* swallow the work-cap interrupt | the cap is checked after the call | — | 0.536 (= honest plan-first; stops at the cap) |
| *new:* forge result file + `os._exit` / `atexit` | token + exit status + `os._exit` | — | −0.840 (all rejected or out of work) |
| *new:* rewrite the evaluator file mid-run | workers run the in-memory source | — | 0.534 (= plan-first: no effect) |

Full-horizon planning before the first move is no longer a loophole: every
planning tick before the first move costs one waiting step per agent. What
remains of its score (0.535, below the reference on every experiment's
primary metric) is that of an honest think-then-move policy. The control
`s_think_then_move` (search within each tick's budget while waiting) scores
0.511.

## Shortcuts left open

- **In-process introspection.** The planner runs in the same process as the
  worker's meter. Code that reaches into the meter's closure cells or the
  worker's frames could reset the event count or edit the recorded path. The
  parent re-checks legality and goals, so only cost and work could be forged,
  but doing so requires deliberately reading evaluator internals. Closing it
  needs OS-level sandboxing, so the separate grader must catch it.
- **Work outside the Python meter.** C extensions, native libraries or
  subprocesses doing the search, and single builtin calls (one event however
  much work they do), are not metered. The container ships no numeric
  libraries. `CONSTRAINTS.md` forbids moving planning out of the meter.
- **Reading the hidden evaluator.** A planner that reads `eval/test/` at test
  time pays for that work in `make_planner`/`step`, and at import it is capped
  at 200k events. A plan cache for the hidden instances would need the hidden
  source before test time, so this relies on `eval/test/` staying hidden.
- **Implementation speed counts.** Faster Python code buys more search per
  tick, exactly as a faster C++ implementation does under the paper's
  millisecond cutoffs. This is honest but is not algorithmic progress.

## Headroom and baselines

The reference sits at the bound of none of its scored metrics. Its
`realtime_score` is 0.51 / 0.55 / 0.72 (bound 1), success 0.80 / 0.80 / 0.75
(bound 1), log cost 1.37 / 1.04 / 0.62 (bound 0), and log work 2.13 / 2.13 /
2.06. The headroom is exactly where the paper's own method falls short:
solution quality under tight cutoffs, plus success when the one-step generator
stalls (some instances go unsolved even by full-horizon search within the
cap). The rotation variant shows the room is reachable (0.73 / 0.75 / 0.80),
so no extra experiment was needed. No metric is stuck across methods. The
restart baseline is clearly below the reference on the congested grids (0.125
vs 0.508). On random-32-32-20 the gap is smaller (0.673 vs 0.724), because
greedy one-step planning solves most low-density instances. The frozen
full-horizon row lies above the reference, as an offline planner should, since
its cost has no waits.

Weights stay 0.34 / 0.33 / 0.33. Each experiment tests a distinct part of the
claim (the tight budget, the cutoff sweep, the standard benchmark map), and
nothing in the results argued for re-weighting. `scoring/reference.json`
keeps the recorded paper-level `success_rate` targets unchanged (real-time =
full-horizon = 1.0, restart lower). The paper reports no number for the other
metrics, so those entries are this reproduction's values, with notes on the
scaling and the reproduced success.

## What I could not fix

- **The generator is weak.** The reproduction's PIBT-style generator stalls
  far more often than the paper's PIBT, and the lazy constraint search then
  explodes. With 14 agents on random-32-32-20 nothing solves within the cap,
  so the benchmark experiment uses 6–12 agents (the paper goes to 400). This
  is the paper's method as reproduced; fixing it would change the reference
  method, and it is left as the main research direction.
- **Train and test differ by sampling.** The slices are disjoint samples of
  the same generators. Per experiment the reference differs by up to 0.13 in
  `realtime_score` (train easier on the scaled grids, harder on
  random-32-32-20; overall D 0.626 vs 0.571). The restart baseline differs
  more on random-32-32-20 (0.364 vs 0.673). I did not tune seeds to match.
- **Meter counts are tied to the Python version.** Line-event counts are
  specific to the CPython version (the container uses 3.11). They matched a
  3.12 run to three decimals here, but the frozen rows are recomputed at test
  time rather than stored for that reason.
- **The hidden test runs planners.** It runs every registered planner and the
  two comparators online (about a minute here). It does not train anything.
  The 30-minute per-episode wall-clock limit is only a safety net and never
  enters a score.
- **The old audit is obsolete.** The cases in `redteam/` from the previous
  audit target the old artifact interface; `REDTEAM.md` describes the old
  evaluator.
