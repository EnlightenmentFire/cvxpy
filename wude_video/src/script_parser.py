"""Parse wude.script into a structured list of segments / lines / cues.

Subtitle text keeps the correct characters; TTS text gets homophone
substitutions so the voice model reads classical names and polyphones right.
"""
import json
import re
import sys
from pathlib import Path

# Global TTS substitutions (subtitle keeps the left side).
# Order matters: longer keys first.
TTS_GLOBAL = [
    ("燕昭王", "烟昭王"), ("燕国", "烟国"),
    ("正朔", "蒸朔"),
    ("封禅", "封善"), ("受禅", "受善"), ("禅让", "善让"),
    ("颛顼", "专须"),
    ("兒宽", "倪宽"),
    ("共工", "工工"),          # 按委托方要求读 gōng gōng
    ("包羲", "包希"),
    ("成纪", "成记"),
    ("北畤", "北志"),
    ("刻削", "刻薛"),
    ("顾颉刚", "顾杰刚"),
    ("眭弘", "虽弘"),
    ("少昊", "绍浩"),
    ("碣石", "杰石"),
    ("朝贺", "潮贺"),
    ("黄龙见", "黄龙现"),
    ("更名", "耕名"), ("更印章", "耕印章"), ("悉更", "悉耕"),
    ("驺子", "邹子"),
    ("夜号", "夜豪"),
    ("著赤帝", "住赤帝"), ("著符", "住符"),
    ("伯而不王", "霸而不望"),
    ("任知刑", "任智刑"), ("以彊", "以强"),
    ("间于木火", "见于木火"),
    ("吕不韦", "吕不维"),
    ("谦让未遑", "谦让未黄"),
    ("自绌", "自触"), ("而绌", "而触"),
]

INLINE = re.compile(r"\{([^{}|]+)\|([^{}|]+)\}")


def split_inline(s):
    """'{兒|倪}宽' -> ('兒宽', '倪宽')"""
    sub = INLINE.sub(lambda m: m.group(1), s)
    tts = INLINE.sub(lambda m: m.group(2), s)
    return sub, tts


def cn_quotes(s):
    """ASCII double quotes -> Chinese curly quotes, alternating open/close."""
    out, open_ = [], True
    for ch in s:
        if ch == '"':
            out.append("\u201c" if open_ else "\u201d")
            open_ = not open_
        else:
            out.append(ch)
    return "".join(out)


def tts_text(s):
    for a, b in TTS_GLOBAL:
        s = s.replace(a, b)
    # quotes/brackets are not spoken
    s = s.replace("“", "").replace("”", "").replace('"', "")
    s = s.replace("「", "").replace("」", "").replace("《", "").replace("》", "")
    return s


def parse_kv(tokens):
    d = {}
    for t in tokens:
        if "=" in t:
            k, v = t.split("=", 1)
            d[k] = v
        else:
            d.setdefault("_args", []).append(t)
    return d


def parse(path):
    segs = []
    cur = None
    pending = []
    lines_all = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("=="):
            parts = [p.strip() for p in line[2:].split("|")]
            meta = parse_kv(parts[2].split()) if len(parts) > 2 else {}
            cur = {"id": parts[0], "title": parts[1], "theme": meta.get("theme", "silk"),
                   "lines": []}
            segs.append(cur)
            continue
        if line.startswith("@>"):
            toks = line[2:].split()
            cue = {"cmd": toks[0], **parse_kv(toks[1:]), "at": "end"}
            cur["lines"][-1].setdefault("cues_end", []).append(cue)
            continue
        if line.startswith("@"):
            toks = line[1:].split()
            cue = {"cmd": toks[0], **parse_kv(toks[1:])}
            if "text" in cue:
                cue["text"] = cn_quotes(cue["text"])
            pending.append(cue)
            continue
        kind, body = line[0], line[2:].strip()
        src = None
        if kind == "Q":
            src, body = [x.strip() for x in body.split("||", 1)]
        sub, tts = split_inline(body)
        sub = cn_quotes(sub)
        ln = {
            "id": f"{cur['id']}_{len(cur['lines']):02d}",
            "seg": cur["id"],
            "kind": kind,
            "text": sub,
            "tts": tts_text(tts),
            "src": src,
            "cues": pending,
        }
        pending = []
        cur["lines"].append(ln)
        lines_all.append(ln)
    if pending:  # trailing cues -> attach to the end of the last line
        for c in pending:
            c["at"] = "end"
        segs[-1]["lines"][-1].setdefault("cues_end", []).extend(pending)
    return segs


def spoken_len(s):
    return len(re.sub(r"[，。；：？！、,.;:?!\"“”「」《》（）()·…—\s]", "", s))


if __name__ == "__main__":
    segs = parse(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else None
    total = 0
    for s in segs:
        n = sum(spoken_len(l["text"]) for l in s["lines"])
        total += n
        print(f"{s['id']:>3} {s['title']:<22} lines={len(s['lines']):>3} chars={n}")
    print("total spoken chars:", total)
    if out:
        Path(out).write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding="utf-8")
