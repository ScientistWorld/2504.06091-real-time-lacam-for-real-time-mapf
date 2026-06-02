#!/bin/bash
# Re-score method output artifacts on the held-out test evaluation slice.

set -euo pipefail
cd /home/user

python eval/test/evaluate.py \
  --rt "${RT_ARTIFACT:-outputs/rt_lacam.json}" \
  --rt-budget3 "${RT_BUDGET3_ARTIFACT:-outputs/rt_lacam_budget3.json}" \
  --full "${FULL_ARTIFACT:-outputs/full_lacam.json}" \
  --naive "${NAIVE_ARTIFACT:-outputs/naive_rt_lacam.json}" \
  --naive-budget3 "${NAIVE_BUDGET3_ARTIFACT:-outputs/naive_rt_lacam_budget3.json}" \
  --movingai-rt "${MOVINGAI_RT_ARTIFACT:-outputs/movingai_rt_lacam.json}" \
  --movingai-full "${MOVINGAI_FULL_ARTIFACT:-outputs/movingai_full_lacam.json}" \
  --movingai-naive "${MOVINGAI_NAIVE_ARTIFACT:-outputs/movingai_naive_rt_lacam.json}" \
  --train-scores scoring/scores_train.json \
  --out scoring/scores_test.json
