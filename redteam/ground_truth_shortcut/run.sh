#!/bin/bash
set -euo pipefail
cd /home/user
python3 redteam/audit.py --case ground_truth_shortcut
