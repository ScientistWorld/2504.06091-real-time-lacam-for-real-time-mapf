#!/bin/bash
# Compute job: reproduce the reference end to end -- register the Real-Time
# LaCAM planner, score it (and the evaluators' frozen comparison rows) on the
# train and held-out test slices -- then, when RUN_HARDENING=1, rerun the
# hardening cases (variants and shortcuts) through the final evaluators.

set -euo pipefail
cd /home/user

bash scripts/reproduce.sh

if [ "${RUN_HARDENING:-1}" = "1" ]; then
  python3 redteam/hardened/make_cases.py
  python3 redteam/hardened/run_cases.py
fi

python3 validate.py || echo "validate.py reported problems (see above)"
