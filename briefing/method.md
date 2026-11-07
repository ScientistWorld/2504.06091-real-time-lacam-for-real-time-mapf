# Method

The paper proposes Real-Time LaCAM, an incremental version of LaCAM for
real-time MAPF.

LaCAM performs a lazy depth-first search over joint configurations. Instead of
enumerating all joint moves at once, each configuration generates one successor
at a time using a fast one-step MAPF generator. When a configuration is
revisited, additional action constraints force the generator to explore a new
successor (first constraining one agent's action, then two agents', and so
on). In the limit, the constrained generator covers the same joint action
space as exhaustive DFS, which makes the search complete.

Real-Time LaCAM keeps the DFS state across planning and execution iterations.
At each iteration it continues the existing DFS until the per-iteration
cutoff, recovers the path from the DFS cursor back to the current executed
configuration, and executes the first joint action on that path. After
execution it re-roots the DFS tree at the new current configuration by
reversing the executed tree edge. Because it builds the same search tree as
full-horizon LaCAM, it keeps LaCAM's completeness and total planning effort.

The packaged implementation (`method/rt_lacam.py`) implements this structure:
lazy joint-configuration DFS split into single constrained-generator attempts,
the LaCAM constraint schedule, persistent search state, and re-rooting. The
per-iteration cutoff is read from the evaluator's work clock. The one-step
generator is a deterministic PIBT-style recursive priority-inheritance planner
that honours a forced prefix of agent actions. It is weaker than the PIBT used
in the paper: when greedy one-step planning stalls, the lazy constraint search
can need very many attempts, which limits the agent counts the packaged
planner solves.
