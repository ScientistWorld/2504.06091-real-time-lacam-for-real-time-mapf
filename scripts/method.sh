#!/bin/bash
# Run the paper's Real-Time LaCAM method and full-horizon LaCAM comparator.

set -euo pipefail
cd /home/user

mkdir -p outputs

python method/rt_lacam.py \
  --mode rt \
  --per-iter-expansions "${PER_ITER_EXPANSIONS:-1}" \
  --total-expansion-budget "${TOTAL_EXPANSION_BUDGET:-20000}" \
  --max-steps "${MAX_STEPS:-200}" \
  --output outputs/rt_lacam.json

python method/rt_lacam.py \
  --mode rt \
  --per-iter-expansions "${PER_ITER_EXPANSIONS_WIDE:-3}" \
  --total-expansion-budget "${TOTAL_EXPANSION_BUDGET:-20000}" \
  --max-steps "${MAX_STEPS:-200}" \
  --output outputs/rt_lacam_budget3.json

python method/rt_lacam.py \
  --mode full \
  --total-expansion-budget "${TOTAL_EXPANSION_BUDGET:-20000}" \
  --output outputs/full_lacam.json
