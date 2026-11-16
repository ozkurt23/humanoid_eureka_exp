#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
seed=${1:-924}
[[ "$seed" =~ ^[0-9]+$ ]] || { echo "Kayıt numarası bir tam sayı olmalı." >&2; exit 2; }
random=''
if ((10#$seed > 800)); then random=1; fi
export FANOUT=2 CBEND=.42 CLEAR=.04 CSTR=.075 YIELD=.18 ROLLK=.7
export SEED="$seed" END=55 RANDOM_EVENTS="$random" VARY_RISE="$random"
export RUN=${RUN:-"kosu-$seed"}
exec bash shoot.sh
