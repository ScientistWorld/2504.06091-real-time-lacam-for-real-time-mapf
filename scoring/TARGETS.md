# Targets

Optimize `success_rate` first on `scaled_small_mapf`.

Valid improvements must also preserve:

- `valid_rate`: paths must remain collision-free and legal.
- `mean_expansions`: higher success should not come only from much more search.
- `mean_normalized_cost`: solutions should not become arbitrarily inefficient.

Every submitted method should write path artifacts that `scripts/evaluate.sh`
can score. The primary comparison is against `rt_lacam`, `full_lacam`, and
`naive_rt_lacam` in `scoring/scores.json`.
