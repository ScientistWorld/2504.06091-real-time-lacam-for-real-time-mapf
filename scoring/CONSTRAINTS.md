# Constraints

Methods must solve the same MAPF instances from `data/mapf_benchmarks.py` and
the downloaded MovingAI files referenced there. They must emit explicit
joint-configuration paths. Evaluation rejects paths with illegal moves, vertex
collisions, or edge-swap collisions.

Do not improve scores by changing the benchmark, selectively dropping hard
instances, hiding invalid paths, or scoring wall-clock speed. Expansion counts
are used as the hardware-independent search effort constraint.

The real-time setting matters: methods should make bounded per-iteration
decisions rather than only returning a full-horizon plan after unbounded search.
The packaged evaluation currently checks one-expansion and three-expansion
per-iteration settings.
