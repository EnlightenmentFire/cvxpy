#!/bin/bash
# 下载字体（均为 SIL OFL 许可）：思源宋体/黑体（Noto Serif SC / Noto Sans SC）、马善政楷书、龙藏体、志莽行书
cd "$(dirname "$0")/../fonts" 2>/dev/null || { mkdir -p "$(dirname "$0")/../fonts"; cd "$(dirname "$0")/../fonts"; }
g=https://fonts.gstatic.com/s
dl(){ [ -s "$2" ] || curl -sL -m 180 "$1" -o "$2"; }
dl $g/notoserifsc/v36/H4cyBXePl9DZ0Xe7gG9cyOj7uK2-n-D2rd4FY7SCqyWv.ttf NotoSerifSC-400.ttf
dl $g/notoserifsc/v36/H4cyBXePl9DZ0Xe7gG9cyOj7uK2-n-D2rd4FY7RcrCWv.ttf NotoSerifSC-600.ttf
dl $g/notoserifsc/v36/H4cyBXePl9DZ0Xe7gG9cyOj7uK2-n-D2rd4FY7QrrCWv.ttf NotoSerifSC-900.ttf
dl $g/notosanssc/v41/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaG9_FnYw.ttf NotoSansSC-400.ttf
dl $g/notosanssc/v41/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaG-3FnYw.ttf NotoSansSC-500.ttf
dl $g/notosanssc/v41/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaGzjCnYw.ttf NotoSansSC-700.ttf
dl $g/notosanssc/v41/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaG3bCnYw.ttf NotoSansSC-900.ttf
dl $g/mashanzheng/v18/NaPecZTRCLxvwo41b4gvzkXaRMQ.ttf MaShanZheng.ttf
dl $g/longcang/v21/LYjAdGP8kkgoTec8zkRgrQ.ttf LongCang.ttf
dl $g/zhimangxing/v19/f0Xw0ey79sErYFtWQ9a2rq-g0ac.ttf ZhiMangXing.ttf
ls -la
