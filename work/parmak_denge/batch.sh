#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
for seed in "$@"; do
    randomized=''
    if (( seed > 800 )); then randomized=1; fi
    FANOUT=2 CBEND=.42 CLEAR=.04 CSTR=.075 YIELD=.18 ROLLK=.7 SEED=$seed RANDOM_EVENTS=$randomized VARY_RISE=$randomized RUN=z$seed bash shoot.sh >z$seed.log 2>&1 &
done
wait
