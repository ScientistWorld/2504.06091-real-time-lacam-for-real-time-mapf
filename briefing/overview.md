# Overview

Real-Time LaCAM addresses real-time MAPF, where agents must execute after a
tiny planning budget rather than wait for a full-horizon plan. The key idea is
to keep LaCAM's lazy DFS tree alive across execution steps and re-root that
tree after each executed move.

The packaged reproduction compares full-horizon LaCAM, Real-Time LaCAM, and a
naive real-time restart baseline on scaled congested MAPF instances and a small
public MovingAI subset. The current results demonstrate the core claim:
Real-Time LaCAM matches full-horizon success on all packaged settings while
the naive restart baseline fails on some instances.
