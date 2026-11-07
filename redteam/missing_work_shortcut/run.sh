#!/bin/bash
set -euo pipefail
cd /home/user
python3 redteam/audit.py --case missing_work_shortcut
