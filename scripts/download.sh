#!/bin/bash
# Estimated download size: 8.2 MB. Disk usage after extraction: about 8.1 MB.
# Downloads the public MovingAI MAPF benchmark maps and random scenarios.

set -euo pipefail
cd /home/user

mkdir -p data/downloads
mkdir -p data/downloads/movingai_mapf

cd data/downloads/movingai_mapf

[ -f mapf-map.zip ] || curl -L -o mapf-map.zip https://movingai.com/benchmarks/mapf/mapf-map.zip
[ -f mapf-scen-random.zip ] || curl -L -o mapf-scen-random.zip https://movingai.com/benchmarks/mapf/mapf-scen-random.zip

[ -f random-32-32-20.map ] || unzip -q -o mapf-map.zip
[ -d scen-random ] || unzip -q -o mapf-scen-random.zip
