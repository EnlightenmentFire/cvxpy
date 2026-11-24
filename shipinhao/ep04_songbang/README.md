# 请给我们松绑——五十五个厂长的一封信（改革开放系列 第4期）

微信视频号竖屏（1080×1920，30fps，H.264 + AAC）。

- `稿子与史料核对.md`：旁白全文、时间码、逐条出处与核对结果
- `stills/`：静帧；`audio/samples/`：样音；`out/`：预览片段与成片
- `src/script.py`：旁白稿（唯一来源）；`src/scenes_*.js`：画面；`src/audio_mix.py`：配乐、音效、混音

## 构建
```bash
bash src/get_fonts.sh                              # 字体（SIL OFL）
uv venv --python 3.12 /opt/ttsenv
uv pip install --python /opt/ttsenv/bin/python torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python /opt/ttsenv/bin/python "kokoro>=0.8.2" "misaki[zh]>=0.8.2" soundfile numpy scipy
bash src/build.sh zm_011 1.08                      # 全片：旁白→时间轴→混音→渲染→编码
FROM=186 DUR=30 SKIP_TTS=1 SKIP_MIX=1 bash src/build.sh zm_011 1.08 out/预览.mp4   # 只做一段
```
画面的所有时间点都由 `audio/narration.json`（旁白时间轴）推出；换声音、改稿子后重新构建即可自动对齐。

许可：TTS 为 Kokoro-82M v1.1-zh（Apache-2.0）；字体为 Noto Serif SC / Noto Sans SC / Ma Shan Zheng（SIL OFL）；配乐和音效为程序合成。
