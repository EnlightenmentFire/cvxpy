# 改革开放系列 03 · 雇八个人算不算资本家——傻子瓜子

竖屏 1080×1920 / 30fps。画面是 `web/` 里的一页 HTML，按时间逐帧截图；旁白、配乐、音效都由脚本生成。

```
./fetch_fonts.sh                                   # 字体（OFL）
python tools/make_assets.py                        # 纸纹、省界轮廓
TTS=cosy VOICE=中文男 SPEED=1.0 python tools/build_audio.py   # 逐句配音 + 时间轴（或 TTS=kokoro VOICE=zm_010）
python tools/make_mix.py build                     # 合成配乐、音效并混音
node tools/render.js build/render                  # 逐帧渲染
python tools/finish.py build/render build/mix.wav out/ep03.mp4   # 拼接、压制、混音
python tools/selfcheck.py                          # 导出前自检
```

- 旁白稿：`script.py`（`{屏幕写法|朗读写法}`）；稿子和史料核对见 `out/旁白稿与史料核对.md`。
- 配音：CosyVoice-300M-SFT「中文男」（Apache-2.0）；备选 Kokoro-82M v1.1-zh（Apache-2.0）。
- 配乐、锅铲声：`tools/make_mix.py` 用 numpy 合成，没有第三方素材。
- 省界轮廓数据：阿里云 DataV 行政区划边界（只用了安徽、广东两省）。
