#!/bin/bash
# End-to-end scaled reproduction of Real-Time LaCAM's core claim.

set -euo pipefail
cd /home/user

bash scripts/method.sh
bash scripts/baseline.sh
bash scripts/evaluate.sh
