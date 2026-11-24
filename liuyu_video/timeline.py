# -*- coding: utf-8 -*-
"""由旁白时长生成全片时间轴，并提供字幕分块与词级对点。"""
import json
import re

import script

PRE = 1.0          # 片头环境声
TITLE_CARD = 3.0   # 冷启动之后的片名卡
LEAD = {"S1": 0.45, "S2": 0.45, "S3": 0.45, "S4": 0.45, "S5": 0.45, "S6": 0.5, "S7": 0.45, "S8": 0.45, "S9": 0.45}
END = 4.2

HAN = re.compile(r"[一-鿿0-9]")


class Timeline:
    def __init__(self, meta_path):
        meta = {m["id"]: m for m in json.load(open(meta_path))}
        self.lines = []
        self.by_id = {}
        self.sec_start = {}
        self.sec_end = {}
        t = PRE
        prev_sec = None
        for d in script.LINES:
            sec = d["sec"]
            if sec != prev_sec:
                if prev_sec is not None:
                    self.sec_end[prev_sec] = t
                if prev_sec == "S0":
                    self.title_start = t
                    t += TITLE_CARD
                self.sec_start[sec] = t
                t += LEAD.get(sec, 0.0)
                prev_sec = sec
            m = meta[d["id"]]
            ent = dict(d)
            ent.update(start=t, dur=m["dur"], end=t + m["dur"], words=m["words"])
            ent["char_times"] = self._char_times(d["tts"] or d["text"], m["words"], t)
            self.lines.append(ent)
            self.by_id[d["id"]] = ent
            t += m["dur"] + d["gap"]
        self.sec_end[prev_sec] = t
        self.end_card = t
        self.total = t + END

    @staticmethod
    def _char_times(text, words, t0):
        """每个内容字（汉字/数字）对应的 (起, 止) 绝对时间"""
        seq = []
        for w, a, b, q in words:
            cs = HAN.findall(w)
            if not cs:
                continue
            n = len(cs)
            for i in range(n):
                seq.append((t0 + a + (b - a) * i / n, t0 + a + (b - a) * (i + 1) / n))
        want = len(HAN.findall(text))
        if len(seq) < want:  # 兜底：补齐
            last = seq[-1] if seq else (t0, t0 + 0.2)
            seq += [last] * (want - len(seq))
        return seq[:want]

    # ── 查询 ──────────────────────────────────────────────
    def start(self, id_):
        return self.by_id[id_]["start"]

    def end(self, id_):
        return self.by_id[id_]["end"]

    def word(self, id_, sub, occ=0, end=False):
        """display 文本里 sub 第 occ 次出现时，旁白读到它的时间"""
        ent = self.by_id[id_]
        text = ent["text"]
        idx = -1
        for _ in range(occ + 1):
            idx = text.find(sub, idx + 1)
            if idx < 0:
                raise KeyError(f"{sub!r} not in {id_}")
        k = len(HAN.findall(text[:idx]))
        n = max(1, len(HAN.findall(sub)))
        ct = ent["char_times"]
        k = min(k, len(ct) - 1)
        if end:
            return ct[min(k + n - 1, len(ct) - 1)][1]
        return ct[k][0]

    def line_at(self, t):
        for ent in self.lines:
            if ent["start"] - 0.05 <= t <= ent["end"] + 0.05:
                return ent
        return None

    # ── 字幕 ──────────────────────────────────────────────
    def subtitles(self, maxlen=17):
        out = []
        for ent in self.lines:
            if ent["sec"] == "S9":
                continue
            text = ent["text"]
            ct = ent["char_times"]
            # 先切成小块（保留标点在块尾）；短的「」（人名、标题）不单独成块
            parts = re.findall(r"「[^」]*」[，。？！；：]?|——|[^，。？！；：「」—]+[，。？！；：]?", text)
            chunks = []
            for p in parts:
                if p == "——":
                    if chunks:
                        chunks[-1] = (chunks[-1][0] + "——", chunks[-1][1])
                    continue
                isq = p.startswith("「") and len(HAN.findall(p)) >= 4
                if not isq and chunks and not chunks[-1][1] and not chunks[-1][0].endswith(("，", "。", "？", "！", "；", "：", "——")):
                    chunks[-1] = (chunks[-1][0] + p, False)
                else:
                    chunks.append((p, isq))
            merged = []
            for c, isq in chunks:
                if merged and not isq and not merged[-1][1] and (len(HAN.findall(merged[-1][0] + c)) <= maxlen
                        or len(HAN.findall(merged[-1][0])) <= 3) and not merged[-1][0].endswith(("。", "？", "！", "——")):
                    merged[-1] = (merged[-1][0] + c, False)
                elif merged and isq and not merged[-1][1] and len(HAN.findall(merged[-1][0])) <= 4 \
                        and not merged[-1][0].endswith(("。", "？", "！")):
                    merged[-1] = (merged[-1][0] + c, True)   # “姨母「…」”“《通鉴》「…」”合成一条
                else:
                    merged.append((c, isq))
            k = 0
            for c, isq in merged:
                n = len(HAN.findall(c))
                if n == 0:
                    continue
                a = ct[min(k, len(ct) - 1)][0]
                b = ct[min(k + n - 1, len(ct) - 1)][1]
                k += n
                disp = c.rstrip("，。；：—")
                if disp.endswith("」"):
                    pass
                out.append(dict(t0=a, t1=b, text=disp, quote=isq, line=ent["id"]))
        # 字幕之间不留空洞：把每条延长到下一条开始（同一行内），最长多 0.6 秒
        for i in range(len(out) - 1):
            gap = out[i + 1]["t0"] - out[i]["t1"]
            if out[i]["line"] == out[i + 1]["line"]:
                out[i]["t1"] = out[i + 1]["t0"] - 0.02
            else:
                out[i]["t1"] += min(0.6, max(0.0, gap - 0.1))
        return out


if __name__ == "__main__":
    import sys
    T = Timeline(sys.argv[1] if len(sys.argv) > 1 else "/home/user/work/narr_main/meta.json")
    print(f"total {T.total:.1f}s  title@{T.title_start:.1f}")
    for s in script.SECTIONS:
        print(s[0], f"{T.sec_start[s[0]]:.1f} → {T.sec_end[s[0]]:.1f}")
    subs = T.subtitles()
    print(len(subs), "subtitles; longest:", max(len(x["text"]) for x in subs))
    for x in subs[:12]:
        print(f"{x['t0']:6.2f}-{x['t1']:6.2f} {x['text']}")
    print(T.word("s5b", "二十七"), T.word("s6f", "素畏伏裕"))
