#!/bin/bash
# Compute job: smoke-test and score the scaled Real-Time LaCAM reproduction.

set -euo pipefail
cd /home/user

bash scripts/reproduce.sh
python validate.py --compare
