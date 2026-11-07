#!/bin/bash
# Score every planner registered under outputs/planners/ on the held-out test
# slice (plus the evaluator's frozen comparison rows). Takes no arguments.

set -euo pipefail
cd /home/user

python3 eval/test/evaluate.py --planners-dir outputs/planners --out scoring/scores_test.json
