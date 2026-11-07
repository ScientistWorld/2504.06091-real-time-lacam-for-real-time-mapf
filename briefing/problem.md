# Problem

Multi-Agent Path Finding (MAPF) asks for collision-free paths for several
agents on a shared 4-connected grid. Every agent starts at a cell and has a
goal cell; at every timestep each agent moves to an adjacent free cell or waits.
A joint move is legal only if no two agents end in the same cell (vertex
collision) and no two agents swap cells (edge collision).

This gym studies **real-time** MAPF. The planner is not given time to compute a
complete plan before the agents start. Instead, planning and execution
interleave: at every tick the planner receives the current joint configuration
and must return the next joint configuration within a small, fixed planning
budget. The agents execute that move, and the loop repeats until every agent
stands on its goal. A planner that needs more than one tick's budget for a
decision is late: the agents wait in place for the ticks it overran.

What makes the problem hard:

- In congested settings (narrow corridors, crossings, dense obstacle fields)
  greedy one-step decisions deadlock or livelock, so a real-time planner must
  still make global progress although it only ever commits to one move.
- Tight per-tick budgets trade against solution quality: myopic moves can make
  the executed paths far longer than necessary.
- The total planning effort across the whole episode should stay comparable
  to that of planning the full horizon once.

Success therefore means: legal execution, reaching all goals within the
episode's limits, a short executed sum of costs, and modest total planning
work.

The benchmark consists of small congested grids (corridors with passing
pockets, four-way crossings, dense random grids with 5-7 agents) and the
MovingAI MAPF benchmark map random-32-32-20 with 6-12 agents. These are scaled
down from published benchmark sizes so that pure-Python planners can be
evaluated quickly; the coordination problem stays the same.
