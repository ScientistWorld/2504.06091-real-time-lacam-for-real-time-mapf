# Problem

Multi-Agent Path Finding (MAPF) asks for collision-free paths for multiple
agents moving on a shared grid. Each agent starts at a cell, has a goal cell,
and may move one cardinal step or wait at each timestep. A valid solution must
avoid vertex collisions and edge-swap collisions.

This reproduction focuses on real-time MAPF. The solver receives a small
planning budget, outputs the next joint action, executes that action, and then
replans from the new joint configuration until all agents reach their goals.

Success requires:

- Valid executed paths with no illegal moves or collisions.
- High episode success under bounded per-iteration planning.
- A cumulative search effort comparable to full-horizon planning.
- Nontrivial coordination in congested instances where naive restart replanning
  can deadlock or livelock.

The benchmark uses deterministic scaled-down grid instances with narrow
passages, cross traffic, and random dense maps, plus a small public MovingAI
random-32-32-20 subset. The scale differs from the paper's largest benchmark
scenes so the environment can run quickly, but the problem remains MAPF
coordination under congestion.
