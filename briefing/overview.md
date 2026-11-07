# Overview

Real-Time LaCAM addresses real-time MAPF, where agents must move after a tiny
planning budget instead of waiting for a full-horizon plan. The key idea is to
keep LaCAM's lazy DFS tree alive across execution steps and re-root that tree
after each executed move, which keeps the search complete.

The gym runs every registered planner online inside the evaluator, which meters
planning work, charges overrun decisions as waiting time, and scores the
executed paths. It compares the paper's planner with two evaluator-owned rows,
a full-horizon planner that plans once and a real-time planner that restarts
its search every tick, on small congested grids at two per-tick budgets and on
the MovingAI random-32-32-20 map.

On the held-out slice the reproduction shows the paper's claim. The real-time
planner matches full-horizon success on random-32-32-20 (0.875 for both). On
the congested grids it comes within the full-horizon planner's success
(0.75-0.80 vs 0.85), while restart replanning collapses (0.30). Tight budgets
cost solution quality, the weakness the paper reports, which leaves clear
headroom: realtime_score is 0.52 / 0.56 / 0.81, well below the bound of 1.
