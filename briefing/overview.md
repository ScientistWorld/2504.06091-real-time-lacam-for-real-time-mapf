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
planner solves exactly as many instances as the full-horizon planner in every
experiment (success 0.80 / 0.80 / 0.75), with comparable total planning work,
whereas restart replanning collapses on the congested grids (0.125 / 0.25) and
trails on random-32-32-20 (0.69). Tight budgets cost solution quality, the
weakness the paper reports, which leaves clear headroom: realtime_score is
0.51 / 0.55 / 0.72, well below the bound of 1.
