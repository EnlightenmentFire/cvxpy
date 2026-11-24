"""Write docs/配乐与混音说明.md from the actual build artefacts (plan, selection, ducking, QC)."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from timeline import Timeline
from make_final_audio import plan
from music_gen import PROMPTS, VERSIONS

BUILD = "/home/user/wude_build"
AUD = sys.argv[1] if len(sys.argv) > 1 else f"{BUILD}/final_audio"
out = Path(__file__).parent.parent / "docs" / "配乐与混音说明.md"

NAMES = {"base": "铺底", "push_cold": "推进·秦（冷硬鼓点）", "push_tension": "推进·紧张", "push_warm": "推进·暖",
         "climax": "高潮（全编制）", "ending": "结尾（单件古琴）", "DROP": "鼓声撤掉（静）", "STOP": "骤停一拍"}


def mmss(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


segs = json.load(open(f"{BUILD}/script.json", encoding="utf-8"))
tl = Timeline(segs, json.load(open(f"{BUILD}/voice_post/durations.json")))
sel = json.load(open(f"{BUILD}/music/selection.json"))
duck = json.load(open(f"{AUD}/ducking.json"))
qc = json.load(open(f"{AUD}/qc.json"))["report"] if os.path.exists(f"{AUD}/qc.json") else {}

L = ["# 配乐与混音说明（按《配乐规范》）", ""]
L += ["## 一、题材与情绪", "",
      "本期是思想史 + 王朝更替，归入规范里的「人物命运、历史转折」：古琴 + 低音弦乐铺底，克制、略带苍凉；"
      "按本期要求再加编钟、磬、低鼓做点缀，不用现代流行配乐。", ""]
L += ["## 二、三层起伏（按故事节点切换，段间 2–4 秒交叉淡化）", "", "| 时间 | 层 | 对应内容 |", "|---|---|---|"]
for (t, layer, g, xf) in plan(tl):
    base = layer.split("@")[0]
    L.append(f"| {mmss(t)} | {NAMES.get(base, base)} | 交叉淡化 {xf:.1f}s，增益 {g:+.0f} dB |")
L += ["", "高潮放在轮盘翻面（相克→相生）：旁白停 2.7 秒，编钟连击 + 全编制单独出来；黄龙出现、片尾「终始」"
      "各留 1.6 秒让音乐单独出来。结尾收成单件古琴，余音后约 3 秒黑场。", ""]
L += ["## 三、音乐来源", "",
      "本地 AI 生成：MusicGen（facebook/musicgen-stereo-medium，transformers），每层先生成 2–3 版 30 秒片段，"
      "按「最不抢人声」的量化指标挑选（1–4 kHz 人声频段能量占比、响度平稳度、突发峰值、Whisper 检测是否含人声），"
      "铺底和两种推进层再用音频续写延长，避免听出循环。", "",
      "**授权提醒**：MusicGen 权重是 CC-BY-NC-4.0（非商用）。如果账号有商业变现，请改用「无配乐」版"
      "（同一画面，人声 + 自制音效），在视频号里加曲库音乐（音量 15–25%），或者改用 incompetech 的 CC BY 曲目（需署名）。", "",
      "| 层 | 版本数 | 选用顺序（第一个为主） | 提示词 |", "|---|---|---|---|"]
for layer in PROMPTS:
    ch = sel["choice"].get(layer, [])
    L.append(f"| {NAMES.get(layer, layer)} | {VERSIONS[layer]} | {'、'.join(os.path.basename(p)[:-4] for p in ch)} | "
             f"`{PROMPTS[layer]}` |")
L += ["", "## 四、混音参数", "",
      f"- 旁白整体响度 -16 LUFS，真峰值限制在 -2 dBTP 以内；成片 loudnorm（I=-16, TP=-1.5, LRA=11），两遍线性。",
      f"- 音乐：3 kHz 处削 4 dB（Q=1）；开头淡入 2 秒，结尾淡出 3 秒。",
      f"- 侧链压缩：压缩比 10、起音 15 ms、释放 500 ms（同规范）；阈值 {duck['chosen']['th']}、音乐音量 "
      f"{duck['chosen']['vol']:.3f}——按规范的 ffmpeg 参考值（阈值 0.02）实测压得过深（人声高出 23 dB），"
      f"所以按实测校准到目标区间。",
      f"- 实测：旁白期间人声比音乐高 {duck['chosen']['rep']['voice_minus_music_median']:.1f} dB（中位数；"
      f"10%–90% 分位 {duck['chosen']['rep']['p10']:.1f}–{duck['chosen']['rep']['p90']:.1f} dB）；"
      f"长停顿里音乐回升到比人声低约 {duck['chosen']['pause_gap']:.1f} dB。", ""]
if qc:
    L += ["## 五、导出前自检（实测）", "",
          f"- 成片响度 {qc['mix_lufs']:.1f} LUFS，真峰值 {qc['mix_true_peak_dbtp']} dBTP；旁白 {qc['voice_lufs']:.1f} LUFS。",
          f"- ASR 回读（逐句拼音准确率）：纯人声 {qc['asr_voice_mean_acc']:.3f}，加配乐 {qc['asr_mix_mean_acc']:.3f}，"
          f"模拟手机外放（300–7000 Hz）{qc['asr_phone_mean_acc']:.3f}。",
          f"- 加配乐后比纯人声差 5% 以上的句子：{('、'.join(qc['asr_lines_worse_by_5pct']) or '无')}。",
          f"- 旁白期间音乐突然冒出来（400 ms 电平比前 2 秒中位数高 6 dB 以上）：{len(qc['music_popouts_while_speaking'])} 处"
          f"{('，' + '、'.join(mmss(x) for x in qc['music_popouts_while_speaking'][:12])) if qc['music_popouts_while_speaking'] else ''}。",
          "- 我没法用耳朵听；「高潮那一段有没有起鸡皮疙瘩」需要你听一下单独导出的《高潮片段_轮盘翻面》。", ""]
out.write_text("\n".join(L), encoding="utf-8")
print("wrote", out)
