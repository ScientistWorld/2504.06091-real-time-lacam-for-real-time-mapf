# Problem Definition

## Research Question

How can a multi-agent path finding system choose collision-free next actions for many agents under strict real-time planning budgets while still avoiding deadlock and livelock over the whole episode?

## Why It Matters

Warehouse robots and other large multi-robot systems cannot always wait for a complete full-horizon plan before acting. A useful real-time MAPF solver must make frequent bounded-latency decisions in congested environments without losing the ability to eventually route all agents to their goals.

## Success Criteria

- Produces valid one-step joint actions at each planning iteration with no vertex or edge collisions.
- Maintains high episode success rate under millisecond-scale per-iteration planning cutoffs.
- Has cumulative planning time comparable to a strong full-horizon planner rather than accumulating large replanning overhead.
- Avoids deadlock and livelock, so failures are due to explicit time/resource limits rather than repeated cyclic behavior.
- Reports solution quality so that improved success is not achieved by unboundedly inefficient paths.
# Problem

Multi-Agent Path Finding (MAPF) asks for collision-free paths for multiple
agents moving on a shared grid. Each agent starts at a cell, has a goal cell,
and may move one cardinal step or wait at each timestep. A valid solution must
avoid vertex collisions and edge-swap collisions.

This reproduction focuses on the real-time MAPF setting. The solver receives
only a small planning budget before it must output the next joint action. It
then replans from the new joint configuration until all agents reach their
goals.

The benchmark uses deterministic small grid instances with narrow passages,
cross traffic, and random dense maps. They are scaled down from the paper's
standard MAPF benchmark evaluation so experiments fit in short CPU/GPU jobs,
but they preserve the relevant difficulty: agents must coordinate through
congestion rather than follow independent shortest paths.
