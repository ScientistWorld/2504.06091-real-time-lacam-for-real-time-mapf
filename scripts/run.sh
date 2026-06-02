#!/bin/bash
# Compute job: score the visible train and held-out test evaluation slices.

set -euo pipefail
cd /home/user

bash scripts/evaluate_train.sh /home/user/checkpoints
bash scripts/evaluate_test.sh /home/user/checkpoints
