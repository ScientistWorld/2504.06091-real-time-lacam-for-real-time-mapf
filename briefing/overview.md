# Overview

- **Paper ID:** 2504.06091
- **Title:** Real-Time LaCAM for Real-Time MAPF
- **Domain:** Multi-Agent Path Finding / Real-Time Planning
- **TL;DR:** The paper adapts LaCAM into a real-time MAPF planner that replans under millisecond per-step cutoffs while preserving the success-rate and cumulative-runtime behavior of full-horizon LaCAM.

## Short Summary

The paper studies multi-agent path finding (MAPF) when agents must repeatedly choose their next joint action after only a small bounded planning interval. Existing windowed and real-time MAPF approaches can be fast but are generally incomplete, which means they can deadlock or livelock in congested settings. Real-Time LaCAM reuses one incremental search across execution steps and reroots that search at the agents' current configuration after each executed move. The authors report that this preserves the success rate and total planning time of full-horizon LaCAM, even with per-iteration cutoffs from 0.01 ms to 100 ms, while naive real-time replanning from scratch fails more often on difficult maps.

## Key Results

- Across the benchmark maps in Figure 2, all Real-Time LaCAM cutoff settings are reported to overlap full-horizon LaCAM in success rate and total cumulative planning time.
- The real-time evaluations use per-iteration cutoffs of 0.01, 0.1, 1, 10, and 100 ms with a 60-second cumulative planning timeout.
- The paper reports a solution-quality tradeoff: on random-32-32-20 and warehouse maps, very small cutoffs can yield 10-100x worse normalized solution cost.
# Overview

Real-Time LaCAM addresses real-time multi-agent path finding, where agents must
execute after a tiny planning budget rather than wait for a full-horizon plan.
The paper's key idea is to keep LaCAM's lazy DFS tree alive across execution
steps and re-root that tree after each executed move.

The packaged reproduction runs a scaled benchmark suite and compares
full-horizon LaCAM, Real-Time LaCAM, and a naive real-time restart baseline. The
current implementation demonstrates the core claim on small congested MAPF
instances: Real-Time LaCAM matches full-horizon success while the naive restart
baseline fails on some instances.
