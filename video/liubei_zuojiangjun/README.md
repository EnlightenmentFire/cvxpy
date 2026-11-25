# 乱世起家录 · 刘备篇 3：左将军与煮酒论英雄（选题 70）

微信视频号竖屏视频，1080×1920 / 25 fps / H.264 + AAC 128k，约 12 分钟。画面全部由代码渲染（skia），配乐与音效全部为 numpy 程序合成的原创音乐，旁白为 Qwen3-TTS（Apache-2.0）克隆的「托克维尔」设计音色。

| 文件 | 作用 |
| --- | --- |
| `src/script_data.py` | 旁白稿（数据源）：每句旁白、读音改写、古文卡/类比卡/三问卡、画面 cue |
| `src/tts.py` | Qwen3-TTS-12Hz-1.7B-Base ICL 克隆（参考音 18 秒），逐句合成，卡中位基频 80–108 Hz |
| `src/voice_post.py` | 去静音、句内停顿 ≤0.32 s、rubberband R3 变速 1.18、高通、归一 |
| `src/asr_check.py` | faster-whisper 回读，无调拼音比对 |
| `src/timeline.py` | 按旁白实长排时间轴、卡片窗口、字幕块 |
| `src/gfx.py` / `src/geo.py` / `src/scenes.py` | 图元、地图（AWS Terrarium 高程 + Natural Earth 河流，均为公共数据）、22 个分镜 |
| `src/render.py` | 合成与分段渲染 |
| `src/audio.py` | 旁白拼接、配乐与音效合成、闪避、增益 + 4 倍过采样真峰值限幅到 -15 LUFS / ≤-1.5 dBTP |
| `src/final_mux.sh` | 两遍 x264（<100 MB）、`aresample=async=1` 混流、音视频时长核对 |
| `src/cover.py` / `src/export_docs.py` | 封面；旁白稿、sentences.json/txt、字幕 srt |
| `史实核对.md` / `发布包.md` | 原文核对与改动说明；标题、简介、话题 |

## 重新生成

```bash
pip install skia-python soundfile scipy pypinyin praat-parselmouth faster-whisper transformers==4.57.3 accelerate==1.12.0 librosa onnxruntime einops
pip install --no-deps qwen-tts==0.1.1   # 其依赖 sox 只用于 25Hz 分词器，可放一个空的 sox.py 占位
export WORK=/tmp/claude-0/work            # 参考音放在 $WORK/ref/ref_voice.wav
python3 src/tts.py && python3 src/voice_post.py && python3 src/asr_check.py
python3 src/audio.py
for i in 0 1 2 3; do python3 src/render.py seg $i 4 & done; wait
bash src/final_mux.sh <输出目录> 左将军与煮酒论英雄
```
地形与河流数据的下载、底图生成脚本见 `src/geo.py` 与 `dem/`（在 $WORK/dem 下运行）。
