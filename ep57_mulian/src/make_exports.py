"""Write text deliverables into an export dir: sentences.json/txt, narration.srt, 脚本.md, 发布包.md"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scenes import QUOTES

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
tl = json.load(open(f"{WORK}/timeline.json"))
lines = tl["lines"]


def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"


def mmss(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


json.dump([dict(id=d["id"], text=d["say"], subtitle=d["sub"] or d["say"], kind=d["k"], pause_after=d["gap"],
                start=d["t0"], end=d["t1"]) for d in lines],
          open(f"{OUT}/sentences.json", "w"), ensure_ascii=False, indent=1)
open(f"{OUT}/sentences.txt", "w").write("\n".join(d["say"] for d in lines) + "\n")
with open(f"{OUT}/narration.srt", "w") as f:
    for i, d in enumerate(lines, 1):
        f.write(f"{i}\n{ts(d['t0'])} --> {ts(d['t1'])}\n{d['sub'] or d['say']}\n\n")

shot_q = {}
for k, (cols, src, bh) in QUOTES.items():
    shot_q[k] = ("".join(cols).replace("︙", "……"), src, bh)
sec_names = dict(a="开篇钩子", b="壹 · 一碗饭（故事）", c="贰 · 一句话（非汝一人力所奈何）", d="叁 · 一个日子（七月十五·自恣）",
                 e="肆 · 一份孝", f="伍 · 一个节日（历史）", g="陆 · 一条河（收束）")
md = ["# 第 57 期 目连救母与盂兰盆 · 定稿旁白\n",
      f"成片时长 {mmss(tl['total'])}；旁白 {sum(len(re.sub(r'[，。？！：；、“”《》\\s]', '', d['say'])) for d in lines)} 字。"
      "【引】为经文原句（引文卡显示繁体原文、出处与白话）。\n"]
cur = None
for d in lines:
    if d["id"][0] != cur:
        cur = d["id"][0]; md.append(f"\n## {sec_names[cur]}（{mmss(d['t0'])}）\n")
    tag = "【引】" if d["k"] == "q" else ""
    extra = ""
    if d["k"] == "q" and d["shot"] in shot_q:
        o, s, b = shot_q[d["shot"]]
        extra = f"  \n  　屏幕：「{o}」——{s}"
    md.append(f"- `{mmss(d['t0'])}` {tag}{d['say']}{extra}")
open(f"{OUT}/脚本.md", "w").write("\n".join(md) + "\n")

pub = f"""# 发布包（第 57 期）

**不要发布、不要上传**，以下供 Seth 选用。

## 标题（推荐第 1 个）
1. 神通第一的弟子，为什么救不了自己的母亲？
2. 中元节和盂兰盆，到底是怎么来的？
3. 一个人的力量不够时，佛陀给了什么办法？

## 简介
《佛说盂兰盆经》里，神通第一的目连看见母亲受苦，递过去的饭却化成了火炭。佛陀说：“非汝一人力所奈何。”——不是你一个人的力量能做到的。
这一期把目连救母当作经典故事来讲，讲清三层寓意，再讲七月十五的自恣日、佛教与孝道，以及盂兰盆会与道教中元如何在民间合流。
一个人的力量总有尽头；孝与慈悲，往往要很多人一起才能完成。

（经文依《大正藏》本；历史说法均标出处，后世追记与学术争议如实说明。）

## 话题
#目连救母 #盂兰盆 #中元节 #佛经故事 #传统文化 #孝道 #七月半

## 声明与标识
- 选「含有 AI 生成内容」：旁白为 AI 合成配音（Qwen3-TTS，Apache-2.0；音色为设计音色，不克隆真人），画面右上角有「AI配音 · 经典故事演绎」角标。
- 画面为程序绘制的示意插画；地图为示意，不表示疆界；敦煌写本为示意。
- 配乐与音效为本片程序原创合成（古琴、箫、磬音色均为算法生成，无第三方采样），无需署名；另附无配乐版。
- 字体：思源宋体 / 霞鹜文楷 / 马善政楷书，均为 SIL OFL，可商用。

## 成片
- 时长 {mmss(tl['total'])}，1080×1920，25 fps，H.264 + AAC，-15 LUFS。
"""
open(f"{OUT}/发布包.md", "w").write(pub)
print("exports written to", OUT)
