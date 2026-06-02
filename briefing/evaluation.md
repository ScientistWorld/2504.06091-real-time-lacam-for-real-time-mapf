# Evaluation

`scripts/evaluate.sh` reads solver artifacts from `outputs/*.json` and invokes
only code in `eval/` plus problem utilities in `data/`. It does not import
`method/`, so future agents can replace the method as long as they emit the
same artifact format.

Each artifact contains a list of explicit joint-configuration paths. The
evaluator independently checks path validity and computes:

- `success_rate`: fraction of instances ending at all goals with a valid path.
- `valid_rate`: fraction of instances with legal moves and no collisions.
- `mean_normalized_cost`: mean sum-of-costs divided by the sum of individual
  shortest path lengths; failed, invalid, or omitted instances receive a
  deterministic instance-size penalty.
- `mean_expansions`: mean generated-successor expansion count, used as a
  hardware-independent search effort constraint.
- `instances`: number of benchmark instances scored.

The core claim is supported when a bounded real-time solver matches a
full-horizon comparator on success and search effort, while a restart-from-
scratch real-time baseline has lower success on the same instances.

The packaged score file includes two scaled deterministic settings and one
public MovingAI random-32-32-20 four-agent setting.
