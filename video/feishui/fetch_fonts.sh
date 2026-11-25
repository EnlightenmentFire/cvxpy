#!/bin/bash
# 思源宋体 / 思源黑体（Noto Serif SC / Noto Sans SC，SIL OFL 1.1）
mkdir -p "$(dirname "$0")/fonts" && cd "$(dirname "$0")/fonts"
curl -L -o NotoSerifSC.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifsc/NotoSerifSC%5Bwght%5D.ttf"
curl -L -o NotoSansSC.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"
