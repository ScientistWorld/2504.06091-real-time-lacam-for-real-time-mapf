# All quality variants

All fourteen candidates were executed with the original tasks, budgets, limits, and evaluator. No reported effort was changed. These are exploratory checks; every candidate is reported, including failures. Exact metrics and train results are in each linked score file and `summary.json`.

Triplets are scaled budget 1, scaled budget 3, MovingAI. N is normalized cost and E is expansions. D is the raw coefficient-weighted diagnostic described in `../REDTEAM.md`; the external ranking implementation was unavailable.

| Variant | Actual change | Success | N | E | D (diagnostic) |
| --- | --- | --- | --- | --- | --- |
| [quality_agent_id](quality_agent_id/scores_test.json) | Agent ID priority | 0.5, 1, 1 | 3.891026, 8.160256, 1.017182 | 124, 155.5, 40.333333 | -30.875801 |
| [quality_reverse_agent_id](quality_reverse_agent_id/scores_test.json) | Reverse agent ID priority | 0.5, 0.5, 1 | 3.891026, 3.660256, 1.017182 | 125.5, 320.5, 40.333333 | -47.231801 |
| [quality_initial_distance](quality_initial_distance/scores_test.json) | Initial-distance priority | 0.5, 1, 1 | 3.891026, 8.160256, 1.017182 | 124, 155.5, 40.333333 | -30.875801 |
| [quality_farthest](quality_farthest/scores_test.json) | Farthest-first dynamic priority | 0.5, 1, 1 | 3.891026, 8.160256, 1.017182 | 124, 155.5, 40.333333 | -30.875801 |
| [quality_degree](quality_degree/scores_test.json) | Prefer higher-degree cells on distance ties | 1, 1, 1 | 3.99359, 2.11859, 1.017182 | 38, 38, 43.333333 | -10.206525 |
| [quality_farthest_degree](quality_farthest_degree/scores_test.json) | Farthest priority and degree ties | 0.5, 1, 1 | 3.698718, 8.240385, 1.024055 | 121.5, 156, 41 | -30.728966 |
| [quality_backtrack_fix](quality_backtrack_fix/scores_test.json) | Restore recursive reservations on failed branches; honest alternative the test cannot tell apart | 1, 1, 1 | 3.974359, 2.035256, 1.017182 | 37.5, 37.5, 40.333333 | -9.802217 |
| [quality_reverse_xy](quality_reverse_xy/scores_test.json) | Reverse coordinate ties | 1, 1, 1 | 9.416667, 3.875, 1.024055 | 74.5, 74.5, 40 | -17.698171 |
| [quality_yx](quality_yx/scores_test.json) | Swap coordinate tie ordering | 0.5, 0.5, 1 | 4.198718, 3.660256, 1.017182 | 124.5, 334, 39 | -48.355224 |
| [quality_reverse_yx](quality_reverse_yx/scores_test.json) | Swap and reverse coordinate tie ordering | 1, 1, 1 | 7, 3.208333, 1.017182 | 58, 58, 43.333333 | -14.502884 |
| [quality_goal_traffic](quality_goal_traffic/scores_test.json) | Avoid other agents' goal cells on distance ties; honest alternative the test cannot tell apart | 1, 1, 1 | 3.974359, 2.035256, 1.017182 | 37.5, 37.5, 40.333333 | -9.802217 |
| [quality_reverse_constraints](quality_reverse_constraints/scores_test.json) | Reverse constraint-prefix enumeration | 0.5, 0.5, 0.666667 | 3.602564, 3.602564, 23.182131 | 120.5, 325.5, 329.333333 | -77.377264 |
| [quality_rotations](quality_rotations/scores_test.json) | Allow legal priority-inheritance rotations; genuine improvement | 1, 1, 1 | 2.009615, 1.445513, 1.017182 | 18, 18, 40.333333 | -5.710192 |
| [quality_continue_heading](quality_continue_heading/scores_test.json) | Prefer continuing the previous direction on distance ties | 1, 1, 1 | 4.224359, 2.11859, 1.240453 | 41, 41, 46.666667 | -11.169953 |

The reference has success (1, 1, 1), N (3.974359, 2.035256, 1.017182), E (37.5, 37.5, 40.333333), D -9.802217. Validity and coverage are 1 and duplicates are 0 for all quality candidates.

`quality_backtrack_fix` ties the complete reference test vector and train vector. `quality_goal_traffic` ties the complete test vector while improving scaled train cost/effort. Both are honest alternatives the test cannot tell apart, rather than unreported shortcut ties.

The rotation fix preserves every reference metric and improves scaled cost and actual search work. Its ordinary train metrics also improve. This finite audit does not establish generalization to unseen tasks.
