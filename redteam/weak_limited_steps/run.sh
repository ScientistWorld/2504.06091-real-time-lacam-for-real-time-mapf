#!/bin/bash
set -euo pipefail
cd /home/user
python3 redteam/audit.py --case weak_limited_steps
