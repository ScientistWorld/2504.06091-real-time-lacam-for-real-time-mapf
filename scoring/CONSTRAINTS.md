# Scientist Constraints

## Problem Formulation
The benchmark must remain standard grid MAPF with synchronous discrete timesteps. Agents may move to the four cardinal neighboring cells or wait. Evaluation must reject vertex collisions and edge-swap collisions. All actions have unit cost except waiting at an already reached goal, matching the paper's cost convention.

## Real-Time Protocol
Methods must plan and execute iteratively. At each iteration, the method may use only the configured per-iteration planning cutoff before choosing the next joint action. A method may not precompute a full-horizon plan and then reveal one action at a time while claiming real-time performance. Cumulative planning timeout accounting must count timed-out runs as 60 seconds.

## Benchmark Data
Use the same standard MAPF benchmark family and the same scene-count convention as the paper: 25 scenes per map for the Figure 2-style evaluation. Do not add easier custom maps, remove congested scenarios, or change starts/goals to improve apparent success. If a reduced benchmark is needed for resource reasons, it must preserve congested random and warehouse-style settings.

## Baseline Comparisons
Full-horizon LaCAM is the parity reference for success rate and cumulative planning time. Real-time/windowed comparisons must use the same maps, scenes, movement model, cumulative timeout, and per-iteration cutoff settings. The naive real-time baseline must use the same underlying one-step configuration-generation capabilities as the proposed real-time planner, differing only in whether planning state is preserved across iterations.

## Learned-Policy Setting
For the secondary learned-policy experiment, the pretrained single-step MAPF policy must be fixed across compared methods. Do not improve the policy weights, train on additional data, or replace the policy with a stronger model when measuring whether the real-time wrapper improves the policy baseline.

## Compliance Checklist
- [ ] Evaluation uses synchronous grid MAPF with cardinal moves plus wait.
- [ ] Vertex and edge-swap collisions are counted as invalid.
- [ ] Per-iteration planning cutoffs are enforced before each executed action.
- [ ] No method precomputes a full-horizon plan for a real-time result.
- [ ] Timed-out runs are counted as 60 seconds in cumulative planning time.
- [ ] The Figure 2-style benchmark uses 25 scenes per map or a documented resource-reduced subset that keeps congested maps.
- [ ] Full-horizon LaCAM, real-time methods, and naive real-time baselines use identical maps, starts, goals, and timeout accounting.
- [ ] Learned-policy comparisons use the same fixed pretrained policy for every method.
# Constraints

Methods must solve the same MAPF instances from `data/mapf_benchmarks.py` and
must emit explicit joint-configuration paths. Evaluation rejects paths with
illegal moves, vertex collisions, or edge-swap collisions.

Do not improve scores by changing the benchmark, increasing the number of
instances selectively, hiding invalid paths, or replacing the metric with
wall-clock speed. Expansion counts are used as the hardware-independent search
effort constraint.
