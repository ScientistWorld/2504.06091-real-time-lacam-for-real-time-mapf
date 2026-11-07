# Direction

Stay within real-time MAPF: per-tick bounded decisions executed one move at a
time, completeness under congestion, and good executed solution quality.

Promising directions:

- Better constrained one-step configuration generators. The packaged generator
  stalls often, and the lazy search then needs many attempts. This limits both
  success under the work cap and the agent counts that can be solved.
- Better solution quality under tight per-tick budgets: less myopic execution,
  smarter choice of which move to commit, and combining search memory with
  heuristic learning.
- Cheaper bookkeeping per tick, so more of the budget goes into search.

Out of scope: returning full-horizon plans computed outside the metered calls,
caching plans for specific instances, changing the problem formulation, or
anything listed in `CONSTRAINTS.md`.
