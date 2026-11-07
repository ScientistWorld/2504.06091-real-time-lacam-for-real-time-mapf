#!/bin/bash
# Register the Real-Time LaCAM planner (the paper's method) for evaluation.
# The evaluators run every planner registered under outputs/planners/.

set -euo pipefail
cd /home/user

mkdir -p outputs/planners
cat > outputs/planners/rt_lacam.json <<'JSON'
{"name": "rt_lacam", "entry": "method/rt_lacam.py", "factory": "make_planner"}
JSON
echo "registered outputs/planners/rt_lacam.json"
