# Paper's Method

## Key Contribution

The paper introduces Real-Time LaCAM, a real-time MAPF planner with a completeness guarantee. Its main contribution is to turn LaCAM's full-horizon lazy depth-first search over joint configurations into an incremental search that persists across repeated planning/execution cycles.

## Approach

Real-Time LaCAM keeps a global LaCAM search tree instead of discarding search state after each real-time planning iteration. During a planning step, it continues expanding the same lazy DFS tree until the per-iteration cutoff is reached. The agents then execute the first move on the current partial path.

After execution, the method reroots the maintained tree at the agents' new current joint configuration by reversing the parent pointer along the executed edge. This ensures that backtracking from the latest search node can always recover a path to the current configuration. Because the search tree and lazy constraints are preserved across iterations, revisited configurations receive additional constraints and the method avoids repeatedly exploring the same cyclic choices from scratch.

The configuration generator can be any one-step MAPF planner that supports imposed action constraints. The paper's experiments use PIBT-style one-step generation, and the learned-policy variant replaces PIBT's heuristic ordering with action probabilities from a pretrained single-step MAPF policy before applying collision-shielded PIBT.

## Main Claims

- **Primary claim**: Real-Time LaCAM is complete for real-time MAPF because, across iterations, it builds the same search tree as full-horizon LaCAM up to rerooting.
- **Primary empirical claim**: With millisecond or sub-millisecond per-iteration cutoffs, Real-Time LaCAM matches full-horizon LaCAM's success rate and cumulative planning time on the tested benchmark subset.
- **Constraint claim**: The real-time interface does not sacrifice completeness/success behavior, but solution quality can degrade when the cutoff is too small.
- **Secondary claim**: The same framework can wrap a learned single-step MAPF policy and improve performance relative to using the policy with CS-PIBT alone.
# Method

The paper proposes Real-Time LaCAM, an incremental version of LaCAM for
real-time MAPF.

LaCAM performs a lazy depth-first search over joint configurations. Instead of
enumerating all joint moves at once, each configuration generates one successor
at a time using a fast one-step MAPF generator. When a configuration is revisited
the generator is called with additional action constraints, eventually covering
the same search space as exhaustive DFS.

Real-Time LaCAM keeps this DFS state across planning/execution iterations. At
each iteration it continues the existing DFS for a small budget, reconstructs
the path from the current DFS cursor back to the current executed
configuration, and executes the first joint action on that path. After execution
it re-roots the DFS tree at the new current configuration by reversing the
executed tree edge. This persistent tree and re-rooting step are the central
algorithmic difference from naive real-time replanning, which starts a new DFS
after every move and can repeatedly explore the same states.

This reproduction implements the actual computation: lazy joint-configuration
DFS, constrained successor generation, persistent search state, and re-rooting.
The one-step generator is a deterministic constrained PIBT-style greedy
generator; fully constrained attempts enumerate valid joint actions, preserving
the lazy constrained search behavior needed by LaCAM.
