#!/bin/bash
# Score every planner registered under outputs/planners/ on the visible train
# slice and write scoring/scores.json. Uses only eval/train (no method/ import).

set -euo pipefail
cd /home/user

python3 eval/train/evaluate.py --planners-dir outputs/planners --out scoring/scores.json
