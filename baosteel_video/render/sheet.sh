#!/bin/bash
# sheet.sh <outdir> <name> t1 t2 t3 t4 ...  -> contact sheets of 4 frames
out=$1; name=$2; shift 2; ts=$(IFS=,; echo "$*")
node "$(dirname "$0")/render.js" stills "$ts" "$out" 2>&1 | grep -E "page|Error" | head -10
files=(); for t in "$@"; do files+=("$out/t$(printf '%06.1f' $t).png"); done
i=0; n=0; while [ $i -lt ${#files[@]} ]; do grp=("${files[@]:$i:4}"); in=""; for f in "${grp[@]}"; do in="$in -i $f"; done
 ffmpeg -y -loglevel error $in -filter_complex "hstack=${#grp[@]},scale=$((540*${#grp[@]})):-1" "$out/${name}_$n.png"; i=$((i+4)); n=$((n+1)); done
