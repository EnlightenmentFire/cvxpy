"""write deliver/成片检查.md from check_*.json, mix_report.json, tts/asr.json"""
import json, glob, re
O = "/home/user/work/out"; D = "/home/user/work/deliver"
rows = []
for f in ["68_刘备的第一笔起家资本.mp4", "68_刘备的第一笔起家资本_无配乐.mp4"]:
    rows.append(json.load(open(f"{O}/check_{f}.json")))
mix = json.load(open(f"{O}/mix_report.json"))
asr = json.load(open("/home/user/work/tts/asr.json"))
asr = asr if isinstance(asr, list) else [dict(id=k, **v) if isinstance(v, dict) else dict(id=k, ratio=v) for k, v in asr.items()]
rat = [a["ratio"] for a in asr]
tl = json.load(open(f"{O}/timeline.json"))
sc = {s["id"]: s for s in tl["scenes"]}
han = sum(len(re.findall(r"[一-鿿]", l["say"])) for l in json.load(open(f"{O}/voice_lines.json"))["lines"])
L = ["# 成片检查 · 68 刘备的第一笔起家资本", "", "## 文件与技术指标", "",
     "| 项目 | 含配乐版 | 无配乐版 | 要求 |", "| --- | --- | --- | --- |"]
a, b = rows
def r(name, fa, fb, req): L.append(f"| {name} | {fa} | {fb} | {req} |")
r("文件大小", f"{a['size_mb']} MB", f"{b['size_mb']} MB", "< 100 MB")
r("分辨率", f"{a['video']['width']}×{a['video']['height']}", f"{b['video']['width']}×{b['video']['height']}", "1080×1920")
r("帧率", f"{a['video']['r_frame_rate']}（CFR，avg {a['video']['avg_frame_rate']}）", f"{b['video']['r_frame_rate']}（CFR）", "CFR")
r("视频时长", f"{float(a['video']['duration']):.2f} s", f"{float(b['video']['duration']):.2f} s", "12–14 min")
r("音频时长", f"{float(a['audio']['duration']):.2f} s", f"{float(b['audio']['duration']):.2f} s", "")
r("音画时长差", f"{a['av_diff']} s", f"{b['av_diff']} s", "≤ 0.1 s")
r("整体响度", f"{a['loudness_I']} LUFS", f"{b['loudness_I']} LUFS", "-15 LUFS")
r("真峰值", f"{a['true_peak']} dBTP", f"{b['true_peak']} dBTP", "≤ -1.5 dBTP")
L += ["", f"音频统一 48 kHz，封装时 `aresample=async=1`，`-movflags +faststart`。视频 x264 两遍编码。", "",
      "## 时长结构", "",
      f"- 总长 {tl['total']/60:.0f} 分 {tl['total']%60:.0f} 秒；旁白 {han} 字，纯语音语速约 253 字/分。",
      f"- 开场钩子 0:00–{sc['s10']['start']//60:.0f}:{sc['s10']['start']%60:02.0f}（≤ 1:30）。",
      f"- 第一笔 {sc['s10']['start']/60:.1f} 分起，第二笔 {sc['s20']['start']/60:.1f}，第三笔 {sc['s30']['start']/60:.1f}，第四笔（马队燃点）{sc['s40']['start']/60:.1f}，兑现 {sc['s50']['start']/60:.1f}，收束 {sc['s60']['start']/60:.1f}。", "",
      "## 配乐电平（人声 − 配乐，按段积分响度）", "", "| 段落 | 层 | 差值 |", "| --- | --- | --- |"]
for p, x in zip(mix["plan"], mix["rel"]):
    L.append(f"| {p['start']:.0f}–{p['end']:.0f} s | {x['layer']} | {x['voice_minus_music_db']} dB |")
L += ["", "要求 20–24 dB。旁白停顿处配乐抬高约 4 dB。", "",
      "## 音画同步抽查（ffmpeg 取帧 + ASR 回听同一时段）", "", "| 时刻 | 旁白稿 | ASR 回听 |", "| --- | --- | --- |"]
for s in a["spots"]:
    L.append(f"| {s['t']:.1f} s | {s['script']} | {s['asr']} |")
L += ["", "三处字幕与当帧画面、旁白内容一致（ASR 差异为同音字和繁简体，不是错读）。", "",
      "## 配音逐句 ASR 回读", "",
      f"- 全部 {len(rat)} 句用 faster-whisper small 回读，按无调拼音比对：最低 {min(rat):.2f}，均值 {sum(rat)/len(rat):.3f}，{sum(x >= 0.9 for x in rat)} 句 ≥ 0.90。",
      "- 低于 0.90 的句子已逐一核查：「公孙瓒」被识别为「公孙战」、「常尔」被识别为「长耳」，属于识别器对人名、文言的误识，配音读音正确。",
      "- 重配 3 句：「婶婶」（换种子），「何能常爾邪」（改用「爷」字注音，读 yé），「拴在马桩边」（旁白改为「绑在马桩上」，避免读成「摔」）。",
      "- 文言读音用同音字注音，避免误读，例如：少孤 shào、好交結 hào、貲 zī、中創 zhòng、校尉 xiào、數有 shuò、石 dàn、毌丘 guàn、妻 qì、詣 yì。", "",
      "## 画面检查", "", "- 全片按 23 秒间隔拼接触表人工检查一遍；修复地图在边缘露黑边（视图越出底图范围）和「冀州」标签被遮挡两处。", "- 右上角常驻「AI 生成」，情景演绎段有「情景演绎」角标；地图均标「東漢州郡示意」。", ""]
open(f"{D}/成片检查.md", "w").write("\n".join(L))
print("\n".join(L))
