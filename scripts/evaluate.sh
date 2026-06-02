#!/bin/bash
# Evaluate solver output artifacts using only eval/ and data/.

set -euo pipefail
cd /home/user

python eval/evaluate_mapf.py \
  --rt "${RT_ARTIFACT:-outputs/rt_lacam.json}" \
  --full "${FULL_ARTIFACT:-outputs/full_lacam.json}" \
  --naive "${NAIVE_ARTIFACT:-outputs/naive_rt_lacam.json}" \
  --out scoring/scores.json
