# 兵法 · 第一期《先为不可胜》

微信视频号竖屏视频（1080×1920，30fps，H.264/AAC）。同一句兵法，周亚夫赢了，章邯输了。

## 目录

| 路径 | 内容 |
|---|---|
| `script.py` | 旁白稿（唯一事实来源）：逐行文本、文言/白话标记、多音字替换、停顿 |
| `FACTCHECK.md` | 引文与史实核对记录、两卷异文、推论标注 |
| `sources/` | 维基文库原文（《史记》卷7/10/11/57/58/106、《汉书》卷5、《孙子兵法》） |
| `tools/verify_quotes.py` | 引文逐条对原文（去标点子串匹配） |
| `tools/tts_kokoro.py` | 逐行合成旁白（Kokoro-82M v1.1-zh）；`--dump` 打印读音供多音字检查 |
| `tools/build_timeline.py` | 逐行 wav → `build/timeline.json`（行起止、分段、字幕块）+ `build/vo.wav` |
| `tools/music.py` | 配乐（numpy 现场合成，无外部素材）+ 闪避混音 → `build/audio.wav` |
| `engine.py` `scenes_a/b/c.py` `render.py` | Skia 逐帧渲染：十段场景、字幕、暗角颗粒 |
| `tools/mux.sh` | 画面 + 音轨 → 成片（响度 -16 LUFS） |
| `out/` | 交付物：静帧、样音、成片 |

## 重建

```sh
apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra libegl1 libgl1 ffmpeg
pip install skia-python numpy pillow                       # 渲染
uv venv --python 3.12 .tts && uv pip install --python .tts/bin/python "kokoro>=0.9.4" "misaki[zh]>=0.9.4" soundfile scipy

python tools/verify_quotes.py                               # 引文核对
.tts/bin/python tools/tts_kokoro.py --voice zm_010 --speed 1.2 --qspeed 1.08 --out build/vo_zm_010
.tts/bin/python tools/build_timeline.py --vo build/vo_zm_010
.tts/bin/python tools/music.py
python render.py --stills s3_12:1.0,s6_04:3.2 --out build/stills   # 先看静帧（行id:偏移秒）
python render.py --all --out build/video.mp4 --jobs 4
sh tools/mux.sh
```

换配音（别的 TTS 或真人录音）：按行 id 提供 `xxx/<行id>.wav`，重跑 `build_timeline.py --vo xxx` 之后的步骤即可——
画面所有动画都挂在行 id 上，会自动重新对时。

## 许可

- 旁白：Kokoro-82M v1.1-zh，模型卡标注 Apache-2.0；中文数据由龙猫数据授权提供（见模型卡）。
- 字体：Noto Serif/Sans CJK SC，SIL OFL 1.1。
- 配乐：本仓库 `tools/music.py` 合成，无第三方素材。
- 引文：《史记》《汉书》《孙子兵法》原文，公有领域；录自维基文库。

## 画面规范（系列通用）

暗调底、骨白字、旧金标原文；己方玄黑（骨白描边）、对手暖红。
安全区：顶部 ~230px、底部 ~440px 不放关键信息；字幕基线 y≈1390。
原文大字用繁体（同维基文库），字幕用简体。
