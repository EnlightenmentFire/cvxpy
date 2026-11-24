#!/bin/sh
# All fonts are SIL OFL 1.1 (Google Fonts). Noto Serif SC / Noto Sans SC / Ma Shan Zheng / Long Cang.
cd "$(dirname "$0")/fonts" || exit 1
base=https://raw.githubusercontent.com/google/fonts/main/ofl
for f in "mashanzheng/MaShanZheng-Regular.ttf" "notoserifsc/NotoSerifSC%5Bwght%5D.ttf" "notosanssc/NotoSansSC%5Bwght%5D.ttf" "longcang/LongCang-Regular.ttf"; do
  out=$(basename "$f" | sed 's/%5B/[/;s/%5D/]/'); [ -f "$out" ] || curl -sL -o "$out" "$base/$f"
done
