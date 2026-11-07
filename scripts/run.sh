#!/bin/bash
set -euo pipefail
cd /home/user
python3 redteam/audit.py --all
python3 redteam/summarize.py
