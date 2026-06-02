# Evaluation

## Metrics

- **Success rate**: fraction of MAPF instances solved before the cumulative planning timeout. Higher is better.
- **Cumulative planning time**: sum of planning time over all planning/execution iterations, with timed-out runs counted as the timeout. Lower is better.
- **Per-iteration cutoff compliance**: the configured per-step planning budget in milliseconds. This is a condition of the experiment rather than an optimized metric.
- **Normalized solution cost**: raw solution cost divided by the sum of each agent's individual shortest-path cost. Lower is better.
- **Collision validity**: all executed joint configurations must avoid vertex and edge collisions. Invalid plans should be treated as failures.

## Baselines and Targets

The main comparison is against a full-horizon MAPF solver run once per instance and real-time/windowed baselines that replan during execution. The paper specifically compares against full-horizon LaCAM, naive real-time LaCAM that restarts search every iteration, and PIBT. For the learned-policy setting, the reported comparison is against CS-PIBT post-processing of a pretrained single-step MAPF policy.

The headline target is to match full-horizon LaCAM's success rate and cumulative planning time while operating under per-iteration cutoffs of 0.01, 0.1, 1, 10, and 100 ms. Solution cost should be reported separately because very small cutoffs can preserve success while substantially worsening normalized cost.

## Evaluation Protocol

Evaluate on the standard grid MAPF benchmark subset used by the paper, with 25 scenes per map. The paper discusses results on maps including random-32-32-20 and warehouse, and plots multiple maps in Figure 2. Each real-time method interleaves planning and execution: at every iteration it plans under the configured cutoff, executes the first valid joint action, then repeats until all agents reach their goals or the cumulative 60-second planning timeout is reached.

Use the same starts, goals, maps, agent counts, movement model, and timeout accounting for all methods. Agents may move to cardinal neighbors or wait; all actions have unit cost except waiting at the goal. Report averages or rates over the same scene set for every compared method and include timed-out runs as 60 seconds in cumulative planning time.
# Evaluation

The evaluator reads solver artifacts from `outputs/*.json` and validates the
reported paths independently. It does not import `method/`, so future agents can
replace the method as long as they emit the same artifact format.

Metrics:

- `success_rate`: fraction of instances ending at all goals with a valid path.
- `valid_rate`: fraction of instances with no illegal moves, vertex collisions,
  or edge-swap collisions.
- `mean_normalized_cost`: mean sum-of-costs divided by the sum of individual
  shortest path lengths, computed over solved instances.
- `mean_expansions`: mean generated-successor expansion count. This is the
  machine-independent replacement for wall-clock runtime.
- `instances`: number of benchmark instances scored.

The core claim is supported when Real-Time LaCAM matches full-horizon LaCAM on
success while using bounded per-iteration expansions, and when the naive
real-time restart baseline shows lower success on the same instances.
