# Method

The paper proposes Real-Time LaCAM, an incremental version of LaCAM for
real-time MAPF.

LaCAM performs a lazy depth-first search over joint configurations. Instead of
enumerating all joint moves at once, each configuration generates one successor
at a time using a fast one-step MAPF generator. When a configuration is
revisited, additional action constraints force the generator to explore a new
successor. In the limit, the constrained generator covers the same joint action
space as exhaustive DFS.

Real-Time LaCAM keeps the DFS state across planning and execution iterations.
At each iteration it continues the existing DFS for a small budget, recovers the
path from the DFS cursor back to the current executed configuration, and
executes the first joint action on that path. After execution it re-roots the
DFS tree at the new current configuration by reversing the executed tree edge.

This reproduction implements the paper's computational structure: lazy
joint-configuration DFS, constrained successor generation, persistent search
state, and re-rooting. The one-step generator is a deterministic constrained
PIBT-style greedy generator; fully constrained attempts enumerate valid joint
actions, preserving the lazy constrained search behavior needed by LaCAM.
