#!/bin/bash
# Score the visible naive-restart baseline (baseline/naive_realtime_lacam.py) on
# the train slice for local comparison. The scored comparison rows in
# scoring/scores_*.json come from frozen copies inside the evaluators instead.

set -euo pipefail
cd /home/user

mkdir -p outputs/baseline_planners
cat > outputs/baseline_planners/naive_restart_visible.json <<'JSON'
{"name": "naive_restart_visible", "entry": "baseline/naive_realtime_lacam.py", "factory": "make_planner"}
JSON
python3 eval/train/evaluate.py \
  --planners-dir outputs/baseline_planners \
  --methods-only \
  --out outputs/baseline_scores_train.json
