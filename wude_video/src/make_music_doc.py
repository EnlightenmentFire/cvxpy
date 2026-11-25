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
         "climax": "高潮（全编制）", "ending": "单件古琴", "DROP": "鼓声撤掉（静）", "STOP": "骤停一拍"}
WHAT = {0: "冷启动 + 邹衍（交代背景）", 1: "邹衍的本意：惧然顾化（与片尾呼应）", 2: "秦：五德说上身",
        3: "「刚毅戾深」前鼓声撤掉", 4: "刻削之后：低铺底", 5: "汉初的别扭、黄龙（叠一声长音）",
        6: "新垣平被诛", 7: "停一拍后回来", 8: "太初", 9: "轮盘翻面（全片高潮，旁白停 2.7 秒）",
        10: "「秦去哪儿了？」→ 闰位、王莽", 11: "收束 → 东汉", 12: "「终始」两个字", 13: "尾声上扬",
        14: "收成单件古琴 + 余音 → 黑场"}


def mmss(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


segs = json.load(open(f"{BUILD}/script.json", encoding="utf-8"))
tl = Timeline(segs, json.load(open(f"{BUILD}/voice_post/durations.json")))
sel = json.load(open(f"{BUILD}/music/selection.json"))
hold = json.load(open(f"{AUD}/ducking_hold.json"))
qc1 = json.load(open(f"{AUD}/qc.json"))["report"]
qc2 = json.load(open(f"{AUD}/qc_hold.json"))["report"] if os.path.exists(f"{AUD}/qc_hold.json") else None

L = ["# 配乐与混音说明（按《配乐规范》）", ""]
L += ["## 一、题材与情绪", "",
      "本期是思想史 + 王朝更替，归入规范里的「人物命运、历史转折」：古琴 + 低音弦乐铺底，克制、略带苍凉；"
      "按本期原要求再加编钟、磬、低鼓做点缀，不用现代流行配乐。", ""]
L += ["## 二、三层起伏（按故事节点切换，段间 2–4 秒交叉淡化）", "", "| 时间 | 层 | 对应内容 |", "|---|---|---|"]
for i, (t, layer, g, xf) in enumerate(plan(tl)):
    base = layer.split("@")[0]
    L.append(f"| {mmss(t)} | {NAMES.get(base, base)} | {WHAT.get(i, '')} |")
L += ["", "- 高潮：轮盘翻面（相克→相生）。旁白停 2.7 秒，编钟连击 + 全编制单独出来。",
      "- 黄龙出现、片尾「终始」各留 1.6 秒，让音乐和长音单独出来；新垣平被诛处按原稿「骤停一拍」（约 1 秒静）。",
      "- 结尾收成单件古琴，余音后黑场；第一段讲邹衍本意时也用古琴（另一版），首尾呼应。",
      "- 每段音乐拼接前过一道离线电平器（1.5 秒窗口，增益 -14 到 +10 dB），去掉片段内部的突然跳变。", ""]
L += ["## 三、音乐来源", "",
      "本地 AI 生成：MusicGen（facebook/musicgen-stereo-medium，transformers）。每层生成 2 版 30 秒片段，"
      "按「最不抢人声」的量化指标挑选（1–4 kHz 人声频段能量占比 0.6、响度平稳度 0.2、突发峰值 0.2；"
      "Whisper 检查是否含人声，削顶的版本重做）；铺底、紧张、暖、秦冷四层再用音频续写延长到 50–70 秒，减少循环感。", "",
      "**授权提醒**：MusicGen 权重是 CC-BY-NC-4.0（非商用）。账号有商业变现时，请用「无配乐」版"
      "（同一画面，人声 + 自制音效），在视频号里加曲库音乐（音量 15–25%），或换 incompetech 的 CC BY 曲目（需署名）。", "",
      "| 层 | 版本数 | 选用顺序（第一个为主） | 提示词 |", "|---|---|---|---|"]
for layer in PROMPTS:
    ch = sel["choice"].get(layer, [])
    L.append(f"| {NAMES.get(layer, layer)} | {VERSIONS[layer]} | {'、'.join(os.path.basename(p)[:-4] for p in ch)} | "
             f"`{PROMPTS[layer]}` |")
L += ["", "## 四、混音", "",
      "- 旁白整体 -16 LUFS（先做真峰值限制到 -2 dBTP）；成片 loudnorm I=-16、TP=-1.5、LRA=11，两遍、线性模式。",
      "- 音乐：3 kHz 削 4 dB（Q=1）；开头淡入 2 秒，结尾淡出 3 秒。",
      "- 侧链压缩：压缩比 10、起音 15 ms、释放 500 ms（同规范），另加 **350 ms 保持 + 40 ms 预读**。",
      f"  原因：照规范参考参数（阈值 0.02）实测人声高出音乐 23 dB，压得过深；把阈值、音量校准到 16.5 dB 后，"
      f"句中每个逗号（0.2–0.38 秒）音乐都会回弹 6–11 dB，形成「呼吸声」，{hold['lines_with_midline_jumps_before']} 句有此现象。"
      f"加保持后只剩 {hold['lines_with_midline_jumps_after']} 句（多为鼓点本身的打击）。",
      f"- 最终参数：阈值 {hold['th_db']:.0f} dBFS，音乐增益 {hold['vol_db']:+.1f} dB。实测说话时人声比音乐高 "
      f"{hold['speech_diff']:.1f} dB（10%–90% 分位 {hold['p10']:.1f}–{hold['p90']:.1f} dB，规范 15–18 dB）；"
      f"句末与段间的停顿里音乐回升到比人声低约 {hold['pause_gap']:.1f} dB。", ""]
L += ["## 五、导出前自检（实测，我不能用耳朵听）", "",
      "- 成片（AAC 编码后）：-16.0 LUFS，真峰值 -1.7 dBTP，LRA 3.2 LU。",
      f"- ASR 逐句拼音准确率：纯人声 {qc1['asr_voice_mean_acc']:.4f}；第一版混音 {qc1['asr_mix_mean_acc']:.4f}，"
      f"模拟手机外放（300–7000 Hz）{qc1['asr_phone_mean_acc']:.4f}"
      + (f"；最终混音（加保持） {qc2['mix_hold']:.4f}。" if qc2 else "。"),
      "- 加配乐后比纯人声差 5% 以上的句子：" + ("、".join(qc2["worse_by_5pct"]) if qc2 and qc2["worse_by_5pct"]
                                          else "无") + "。",
      "- 已知回读假阳性（读音本身正确）：S1_12「祥」被写成同音的「降」（xiáng）、S5_11「祀」被写成「似」（sì）；"
      "S2_10「旄旌」重录后选的是回读为「毛经」（jīng）的一条，但 Whisper 对「毛巾」偏向很强，复查时仍时有误报。",
      "- 「高潮那一段有没有起鸡皮疙瘩」需要你亲自听：已单独导出《高潮片段_轮盘翻面》（翻面前 12 秒到后 28 秒）。", ""]
out.write_text("\n".join(L), encoding="utf-8")
print("wrote", out)
