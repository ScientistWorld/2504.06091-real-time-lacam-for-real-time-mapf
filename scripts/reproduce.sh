#!/bin/bash
# End-to-end reproduction: register the method, score it on train and test.

set -euo pipefail
cd /home/user

bash scripts/method.sh
bash scripts/evaluate_train.sh
cp scoring/scores_train.json scoring/scores.json
bash scripts/evaluate_test.sh
