#!/bin/bash
# Run the naive real-time LaCAM baseline that restarts search every step.

set -euo pipefail
cd /home/user

mkdir -p outputs

python baseline/naive_realtime_lacam.py \
  --per-iter-expansions "${PER_ITER_EXPANSIONS:-1}" \
  --total-expansion-budget "${TOTAL_EXPANSION_BUDGET:-20000}" \
  --max-steps "${MAX_STEPS:-200}" \
  --output outputs/naive_rt_lacam.json

python baseline/naive_realtime_lacam.py \
  --per-iter-expansions "${PER_ITER_EXPANSIONS_WIDE:-3}" \
  --total-expansion-budget "${TOTAL_EXPANSION_BUDGET:-20000}" \
  --max-steps "${MAX_STEPS:-200}" \
  --output outputs/naive_rt_lacam_budget3.json
