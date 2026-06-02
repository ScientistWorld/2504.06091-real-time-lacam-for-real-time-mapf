# Experiment Overview

## realtime_mapf_benchmark
Tests whether the real-time system achieves the paper's central benchmark goal: solving the same MAPF instances as the full-horizon reference while operating under strict per-step planning budgets. This experiment also tracks total planning time and path quality so that a method cannot score well by solving instances slowly or with extreme detours.

## realtime_validity_and_budget
Checks that the evaluation is genuinely real-time and that the produced executions are valid MAPF solutions. This experiment exists to guard the benchmark constraints: every action must be chosen within the per-step cutoff, the cumulative timeout must be enforced consistently, and any collision invalidates the run.

## naive_replanning_baseline
Tests whether a real-time planner benefits from retaining useful information between planning iterations. The comparison uses the same problem instances and budgets as the main benchmark, but measures a baseline that starts each planning iteration fresh.

## learned_policy_wrapper
Tests the paper's secondary claim that a real-time planning wrapper can improve a fixed single-step MAPF policy. The purpose is to evaluate whether the policy becomes more reliable under the same random-map setting without changing the policy itself.
# Experiments

`scaled_small_mapf` evaluates whether a real-time MAPF solver can keep solving
congested instances under tiny per-iteration planning budgets. It compares a
persistent real-time solver, a full-horizon solver, and a restart-from-scratch
real-time baseline. The experiment establishes both the benefit metric
(successful completion) and constraints (valid paths, normalized cost, and
search expansions).
