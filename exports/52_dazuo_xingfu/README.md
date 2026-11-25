# 52 打坐与幸福感（静坐的科学 · 第一期）

| 文件 | 说明 |
|---|---|
| `dazuo_xingfu_1080x1920.mp4` | 成片：10:07（607.2 秒），1080×1920，25fps 恒定帧率，H.264 两遍编码 + AAC 128k，含底乐；-15.3 LUFS，真峰值 -1.8 dBTP；92.7 MB |
| `dazuo_xingfu_1080x1920_无配乐.mp4` | 备用：同一画面，只有旁白和音效（开场钟声、手机轻振、朱印闷响），无底乐；-15.3 LUFS，91.6 MB |
| `cover_52.png` | 封面 1080×1920（文字在中部 3:4 安全区） |
| `发布包.md` | 标题三选一、简介、话题、发布勾选项 |
| `FACTCHECK.md` | 每个数字、每句经文的出处与核对结果 |
| `sentences.json` / `sentences.txt` | 逐句旁白稿（序号、字幕文本、送 TTS 文本、场景、起止时间） |
| `narration.srt` | 字幕时间轴 |
| `ASR回读.txt` | 配音逐句 ASR 回读比对 |
| `src/` | 全部生成代码（见下） |

## 声音
- 配音：托克维尔声音。Qwen3-TTS-12Hz-1.7B-Base（Apache-2.0）ICL 克隆，参考音为 18 秒设计音色（与 `claude/tocqueville-america-video-a250yg` 分支 `preview/voice_design_reference.m4a` 相同，即 A0b 设计音色参考），逐句合成，中位音高须在 85–105 Hz，否则换 seed。本会话无 GPU，在 CPU 上跑完。
- 后期：去头尾静音、句内停顿 ≤0.4 秒、rubberband R3 统一变速（保共振峰；经文句不加速）、50 Hz 高通；句间 0.5 秒。
- 开场声音钩子：首帧一声低沉的钟（佛法题材，按 Seth 10:29 修正用钟磬，不用打字声、不用小铃铛），0.3 秒处一下手机轻振，对应画面上「你现在在想什么？」的提示。
- 底乐：全部程序生成（`src/audio.py`）：古琴式拨弦（带吟、下滑音）、低音铺底、箫式气声长音，D 宫五声；大段落开头一声磬。局限段（泼冷水）音乐变稀疏，印照与收束段箫声多一些。没有任何第三方音乐素材，可商用。
- 混音：底乐静态比人声低 20 dB，旁白期间再侧链压低约 3 dB（停顿处回升），即人声下约 -20 到 -23 dB；两遍 loudnorm 到 -15 LUFS（真峰值目标设 -2.2 dBTP，实测 -1.8，留出 AAC 编码余量）；`aresample=async=1`。

## 实测
- 音画同步：两版视频流与音频流都是 607.200 秒，差 0.000 秒；抽查开头（5.4 秒）、中段（288 秒）、结尾（597 秒）三句，画面字幕与 ASR 听写一致。
- ASR 回读：102 句平均拼音匹配 0.992，没有低于 0.85 的句子（`ASR回读.txt`；ASR 输出偶有繁体字，是识别器的问题，不是读错）。
- 语速：2,462 字（不含标点）÷ 旁白跨度 ≈ **245 字/分**，变速 1.114 倍。比 VOICE_SPEC 的 255 略慢：按 255 算全片只有 9.7 分钟，低于 brief 的 10–12 分钟，所以取了折中。要改成 255，设 `TARGET_CPM=255` 从 `voice_post.py` 起重跑即可。
- 底乐：比人声低 20 dB，旁白时再侧链压约 3 dB。

## 画面
全部程序生成的水墨风：宣纸底、淡墨远山与晨雾、随风轻摆的竹、坐禅剪影、朱印标签、卷轴两栏（Goyal 结果）、点阵（46.9%）、墨色条形图、竖排楷书经文逐字显影。收束为人走入街巷。不使用 AI 生图，无真人形象。角标「AI 配音」全程保留。

## 重做步骤（在 src/ 下）
```bash
python tts_clone.py                 # 逐句克隆配音 -> /tmp/claude-0/work/tts/raw
python voice_post.py                # 后期 + 统一变速 -> tts/proc
python render.py timeline           # 按配音时长生成 timeline.json / narration.srt
python audio.py                     # voice.wav / music.wav / sfx.wav
python render.py video silent.mp4   # 4 进程渲染无声视频
python mix.py silent.mp4 dazuo_xingfu_1080x1920.mp4
python mix.py silent.mp4 dazuo_xingfu_1080x1920_无配乐.mp4 --nomusic
python asr_check.py ASR回读.txt
python cover.py cover_52.png
```
如需在 box 上换配音：把逐句 wav（文件名 = sentences.json 里的 id）放进 `VOICE_DIR`，从 `render.py timeline` 往下重跑即可，画面和字幕会按新时长自动对齐。
