#!/bin/bash
# 字体（SIL OFL 1.1）不入库，按需下载
cd "$(dirname "$0")"
curl -L -o NotoSerifSC.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifsc/NotoSerifSC%5Bwght%5D.ttf"
curl -L -o MaShanZheng.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/mashanzheng/MaShanZheng-Regular.ttf"
curl -L -o LXGWWenKai.ttf "https://raw.githubusercontent.com/lxgw/LxgwWenKai/main/fonts/TTF/LXGWWenKai-Regular.ttf"
