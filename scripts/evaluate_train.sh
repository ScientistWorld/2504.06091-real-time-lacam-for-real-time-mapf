#!/bin/bash
# Score every planner registered under outputs/planners/ on the visible train
# slice (plus the evaluator's frozen comparison rows).

set -euo pipefail
cd /home/user

python3 eval/train/evaluate.py --planners-dir outputs/planners --out scoring/scores_train.json
