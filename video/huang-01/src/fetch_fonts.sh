#!/bin/bash
# 下载字体到 fonts/（均为 SIL OFL 1.1）
set -e
cd "$(dirname "$0")/../fonts" 2>/dev/null || { mkdir -p "$(dirname "$0")/../fonts"; cd "$(dirname "$0")/../fonts"; }
for f in "ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf" "ofl/notoserifsc/NotoSerifSC%5Bwght%5D.ttf" "ofl/ibmplexmono/IBMPlexMono-Regular.ttf" \
         "ofl/ibmplexmono/IBMPlexMono-Medium.ttf" "ofl/inter/Inter%5Bopsz,wght%5D.ttf" "ofl/inter/Inter-Italic%5Bopsz,wght%5D.ttf"; do
  out=$(basename "$f" | sed 's/%5B/[/;s/%5D/]/')
  [ -f "$out" ] || curl -sL --retry 3 -o "$out" "https://raw.githubusercontent.com/google/fonts/main/$f"
done
ls -la
