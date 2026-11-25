"""Write the take table (scores + choice) and AAC copies of every take for auditioning."""
import json, os, subprocess, sys
from music import LAYERS

def main(takes_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    sc = json.load(open(os.path.join(takes_dir, "scores.json")))
    ch = json.load(open(os.path.join(takes_dir, "choice.json")))
    chosen = {n.replace("_al", "") for v in ch.values() for n in v}
    rows = ["# 配乐候选（MusicGen stereo-medium，每段 22 秒）", "",
            "分数越低越好：人声检测（ASR 能认出词就重罚）、1–4 kHz 能量占比（越低越不抢人声）、响度起伏、断音；高潮段反过来奖励明显的推起。"
            "选中的片段已统一移调到 A 小调（或其关系大调）。所有候选的试听文件在本目录。", "",
            "**授权提醒：MusicGen 权重是 CC-BY-NC-4.0（非商用）。商用发布请用无配乐版，或换可商用曲库。**", "",
            "| 层 | 片段 | 选用 | 分数 | 1–4kHz 占比 | 起伏 dB | 估计调性 | 移调 | 速度 BPM | 人声检测 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for layer, spec in LAYERS.items():
        for k in sorted([x for x in sc if x.rsplit("_", 1)[0] == layer], key=lambda x: sc[x]["score"]):
            a = sc[k]
            rows.append(f"| {layer} | `{k}` | {'✅' if k in chosen else ''} | {a['score']} | {a['presence']} | {a['stability_db']} | {a['key']} | {a['shift']:+d} | {a['tempo']} | {a['vocals'] or '无'} |")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(takes_dir, k + ".wav"), "-c:a", "aac", "-b:a", "160k",
                            os.path.join(out_dir, k + ".m4a")], check=True)
        rows.append("")
    rows += ["", "提示词：", ""] + [f"- **{k}**：`{v['prompt']}`" for k, v in LAYERS.items()]
    open(os.path.join(out_dir, "README.md"), "w").write("\n".join(rows) + "\n")
    print("wrote", out_dir)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
