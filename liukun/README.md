# 刘琨——一座没有后方的孤城（视频号竖屏 1080×1920 / 30fps）

全片由脚本生成，可整条重跑：

```
src/script.py          旁白稿（唯一来源；kind=q 为朗读的史书原文，show= 为只上画面的原文）
src/tts_prep.py        生成 TTS 输入（同音字替换只影响读音）/ 修剪静音
src/build_timeline.py  按每句音频时长排时间轴 -> audio/timeline.json、out/liukun.srt
src/mix.py             配乐、音效（全部程序合成）+ 旁白混音 -> out/audio_mix.wav
src/core.js scenes_*.js main.js index.html   画面（Canvas，逐帧由时间 t 决定）
src/render.cjs / render_all.sh               Playwright 出帧 -> ffmpeg 两遍编码
src/qa_asr.py          ASR 回听校验读音
sources/               《晋书》卷62、67，《资治通鉴》卷88–91（维基文库原文，校对引文用）
旁白稿.md              便于阅读的稿子（含出处）
```

## 素材与许可

| 项目 | 来源 | 许可 |
|---|---|---|
| 旁白 | CosyVoice-300M-SFT 内置音色“中文男”（未做任何声音克隆） | 代码 Apache-2.0；模型卡（Hugging Face）标注 apache-2.0 |
| 配乐 / 音效 | `src/mix.py` 程序合成（箫、埙、胡笳、弦乐垫底、风声、鸡鸣、鼓、磬） | 自制，无第三方素材 |
| 字体 | Noto Serif SC（思源宋体）、Ma Shan Zheng（马善政毛笔楷书） | SIL OFL 1.1 |
| 地图 | 手工近似坐标绘制的示意图（非测绘底图） | 自制 |
| 史料原文 | 维基文库《晋书》《资治通鉴》 | 公有领域 |

注：CosyVoice 模型卡另有一句免责声明（示例内容“for academic purposes only”），与 Apache-2.0 授权并列；商用前请自行判断，或改用自己录音（`audio/vo/nXXX.wav` 逐句替换后重跑 `build_timeline.py`、`mix.py`、`render_all.sh` 即可）。
