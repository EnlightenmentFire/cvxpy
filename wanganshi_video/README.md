# 选题 36《王安石变法为什么失败》视频号竖屏工程（制作中）

- `src/script_data.py` 全片脚本（数据）；`docs/史料核对.md` 逐条核对；`docs/发布包.md` 标题/简介/话题/声明
- 画面：`gfx.py`（宣纸、水墨、铜钱、人物、印章等程序绘制）、`scenes.py`（36 个场景）、`render.py`（时间线、字幕、引文卡、并行渲染）
- 配音：`tts_clone.py`（Qwen3-TTS Base 克隆托克维尔设计音色）、`voice_post.py`、`regen.py`、`asr_check.py`
- 声音：`music.py`（代码作曲 + FluidSynth/FluidR3_GM，MIT）、`sfx_mix.py`（铜钱、惊堂木、低钟合成；侧链压低；-15 LUFS）
- 成片：`final_encode.py`（两遍 x264，<100 MB，CFR 25fps，aresample=async=1）；`pipeline_final.sh` 一键后半程
