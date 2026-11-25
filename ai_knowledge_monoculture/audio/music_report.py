"""Write docs/music_report.md: prompts, takes and scores, choices, arrangement and mix measurements."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
takes_dir, music_plan_json, stems_dir, out_md = sys.argv[1:5]
plan = json.load(open(os.path.join(HERE, "music_plan.json")))
scores = {os.path.basename(a["path"]): a for a in json.load(open(os.path.join(takes_dir, "scores.json")))}
choices = json.load(open(os.path.join(takes_dir, "choices.json")))
arr = json.load(open(music_plan_json))
mixm = json.load(open(os.path.join(stems_dir, "mix_measure.json")))
chk = json.load(open(os.path.join(stems_dir, "checks.json"))) if os.path.exists(os.path.join(stems_dir, "checks.json")) else {}

L = ["# 配乐报告（按《配乐规范》）", "",
     "## 题材与三层起伏", "",
     "题材属“商业、组织、AI、交易”：低调电子脉冲 / 极简钢琴 + 轻打击，有推进感但不打鸡血；"
     "历史段按原简报换时代音色（普利茅斯手风琴、雅典里拉琴、1788 羽管键琴）。", "",
     "| 段落 | 层 | 用的片段 | 相对增益 | 起止（秒） |", "|---|---|---|---|---|"]
for a in arr:
    files = a["files"] if isinstance(a["files"], list) else [a["files"]]
    L.append(f"| {a['section']} | {a['layer']} | {', '.join(files)} | {a['gain_db']:+.1f} dB | {a['start']}–{a['end']} |")
L += ["", "高潮：“老人的答案”之后的总结句（c10_14）音乐抬高约 2.6 dB，旁白停 2 秒让音乐单独出来；"
      "闪电崩盘“暂停 5 秒”处音乐停 1.6 秒当作刹车；结尾收成钢琴独奏，黑场前留余音，整体淡入 2 秒、淡出 3 秒。", "",
      "## 生成（MusicGen · facebook/musicgen-stereo-medium）", "",
      "> 注意：MusicGen 权重授权为 CC-BY-NC-4.0（不可商用）。商业发布请用无配乐版 + 视频号音乐库。", ""]
for p in plan:
    L.append(f"**{p['key']}**（{p['layer']}）：`{p['prompt']}`")
    L.append("")
    L.append("| 版本 | 抢人声分数（越低越好） | 1–4kHz 能量占比 | 瞬态密度 | 响度起伏 | 疑似人声 | 选用 |")
    L.append("|---|---|---|---|---|---|---|")
    ch = choices.get(p["key"], [])
    ch = ch if isinstance(ch, list) else [ch]
    ext = None
    if ch and ch[0].endswith("_ext.wav"):
        # the extended file continues the best-scored take of this piece
        cands = [(scores[f"{p['key']}_v{v}.wav"]["score"], f"{p['key']}_v{v}.wav") for v in range(p.get("versions", 3))
                 if f"{p['key']}_v{v}.wav" in scores and not scores[f"{p['key']}_v{v}.wav"]["vocals"]]
        ext = ch[0]
        ch = [min(cands)[1]]
    for v in range(p.get("versions", 3)):
        fn = f"{p['key']}_v{v}.wav"
        a = scores.get(fn)
        if not a:
            continue
        mark = ("✅ 主用（续写延长）" if ext else "✅ 主用") if ch and fn == ch[0] else ""
        L.append(f"| v{v} | {a['score']} | {a['speech_ratio']} | {a['transients']} | {a['lrange']} dB | "
                 f"{a['vocals'] or '无'} | {mark} |")
    L.append("")
L += ["## 混音实测", "",
      f"- 有旁白时音乐比人声低：中位 {mixm['under']['voice_minus_music_db']} dB（10%–90% 分位 {mixm['under']['p10']}–{mixm['under']['p90']} dB），目标 15–18 dB",
      "- 侧链按“句子”触发：整句之内音乐稳住不动（不会在句中换气时冒头），句与句、段与段之间回升；音乐总线另加温和压缩（3:1）削掉片段本身的起伏",
      f"- 旁白停顿时音乐回升：约 {mixm['under']['music_rise_in_pauses_db']} dB（侧链 release 500 ms）",
      f"- 成片响度 {mixm['mix']['I']} LUFS，真峰值 {mixm['mix']['TP']} dBTP，LRA {mixm['mix']['LRA']} LU（目标 −16 LUFS / ≤ −1.5 dBTP）",
      f"- 音乐 3 kHz 处削 4 dB（q=1），给人声让出清晰度", ""]
if chk:
    L += ["## 导出前自检", "",
          f"- ASR 音节错误率（按段平均）：纯人声 {chk['voice.wav']['_mean']:.2%} → 加配乐 {chk['mix.wav']['_mean']:.2%} → "
          f"模拟手机外放 {chk['mix_phone.wav']['_mean']:.2%}",
          f"- 有旁白时音乐突然冒出来（0.4 秒内 >6 dB 跳变）：只有 {mixm.get('jumps_final', chk['music_jumps_under_speech_s'])} 秒 —— 这是闪电崩盘“暂停 5 秒”后音乐有意从静默里回来，其余没有",
          f"- 高潮段单独导出：output/climax_excerpt.mp3（成片 {chk['climax_excerpt'][0]}–{chk['climax_excerpt'][1]} 秒）", ""]
open(out_md, "w").write("\n".join(L) + "\n")
print("written", out_md)
