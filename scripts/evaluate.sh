#!/bin/bash
# Evaluate solver output artifacts using only eval/ and data/.

set -euo pipefail
cd /home/user

python eval/evaluate_mapf.py \
  --rt "${RT_ARTIFACT:-outputs/rt_lacam.json}" \
  --rt-budget3 "${RT_BUDGET3_ARTIFACT:-outputs/rt_lacam_budget3.json}" \
  --full "${FULL_ARTIFACT:-outputs/full_lacam.json}" \
  --naive "${NAIVE_ARTIFACT:-outputs/naive_rt_lacam.json}" \
  --naive-budget3 "${NAIVE_BUDGET3_ARTIFACT:-outputs/naive_rt_lacam_budget3.json}" \
  --out scoring/scores.json
