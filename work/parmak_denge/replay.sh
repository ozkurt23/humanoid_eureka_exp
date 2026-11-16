#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
source env.sh
export DIRECT=1 REFLEX=1 TRIGGER=time AMP=1 SQUARE=1 BEND=${CBEND:-.42} PUSHBODY=base_link PERIOD=${CPER:-1.0} STRIDE=${CSTR:-.06} LIFT=.25 LAND=.69 LEAD=.18 RISE=1.15 RATE=10 DAMP=4
export SEED=${SEED:-715} PEN=0 END=${END:-55}
export WIDEN=${WIDEN:-.055} RESUME=1.3 RESTFIRST=0 PRE=.20 SW=${SW:-.31} WIDTH=${WIDTH:-.18} ALPHA=${ALPHA:-1.22} MATCH=.55
"$HOME/env_isaaclab/bin/python" replay.py
