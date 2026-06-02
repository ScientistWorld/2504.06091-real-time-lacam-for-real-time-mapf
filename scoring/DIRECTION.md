# Research Direction

## Research Problem
This benchmark is about real-time multi-agent path finding: choosing the next collision-free joint action for many agents under a strict bounded planning interval, then repeating until all agents reach their goals. The scientific question is how to make this iterative real-time regime reliable in congested settings without giving up the practical latency benefits that motivate real-time planning.

## Core Contribution
The paper's contribution is a complete real-time search framework for MAPF that preserves useful search information across execution steps. Future improvements should stay focused on real-time MAPF completeness, robustness, runtime, and solution quality under repeated bounded planning.

## Approach Scope
Scientist agents may modify the real-time search strategy, the one-step joint-action generator, tie-breaking, constraint ordering, partial-plan selection, cutoff scheduling, or search-state reuse policy. They may also improve the learned-policy wrapper experiment if the pretrained policy itself remains fixed for that comparison. The improvement should still be a real-time MAPF method that produces one executed joint action per planning iteration.

## Out of Bounds
- Replacing the task with full-horizon offline MAPF planning without a real-time execution loop.
- Reporting a method that violates the per-iteration cutoff and only satisfies the cumulative timeout.
- Using a stronger learned policy, extra training data, or a larger model to improve the learned-policy experiment.
- Changing the benchmark maps, starts, goals, collision rules, or cost convention to make instances easier.
- Optimizing only path cost while allowing deadlock, livelock, collision invalidity, or substantially worse success rate.
# Direction

Future work should stay within real-time MAPF and incremental/windowed search.
Reasonable improvements include better constrained one-step generators,
priority ordering, heuristic ordering, or LaCAM-family engineering changes.

Switching to a different problem formulation that ignores real-time execution
or returns only full-horizon plans without bounded per-iteration decisions is
outside the intended direction for this gym.
