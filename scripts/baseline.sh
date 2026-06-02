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

if [ "${RUN_MOVINGAI:-1}" = "1" ]; then
  python baseline/naive_realtime_lacam.py \
    --benchmark movingai \
    --per-iter-expansions "${MOVINGAI_PER_ITER_EXPANSIONS:-3}" \
    --total-expansion-budget "${MOVINGAI_TOTAL_EXPANSION_BUDGET:-50000}" \
    --max-steps "${MOVINGAI_MAX_STEPS:-300}" \
    --output outputs/movingai_naive_rt_lacam.json
fi
