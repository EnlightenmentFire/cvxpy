# -*- coding: utf-8 -*-
"""由配音实际时长生成画面时间轴 timeline.json。

句子边界来自 voice_timing.json（拼接时精确记录）；句内的分屏点、画面事件
用 faster-whisper 的逐字时间戳（words.json）对齐。
"""
import json
import sys


def main(work, out):
    VT = json.load(open(f"{work}/voice/voice_timing.json"))
    W = json.load(open(f"{work}/voice/words.json"))  # [[start, end, word], ...]
    S = {s["id"]: s for s in VT["sentences"]}

    def at(word, after=0.0):
        """第一个在 after 之后、以 word 开头的词的起点。"""
        for a, b, w in W:
            if a >= after - 1e-3 and w.strip().startswith(word):
                return a
        raise KeyError(word)

    s1, s2, s3, s4, s5, s6 = (S[k] for k in ("S1", "S2", "S3", "S4", "S5", "S6"))
    t_cheng = at("城", s2["t0"])          # 城破之后
    t_da = at("打", s3["t0"])             # 打了几个月
    t_cao = at("曹", s4["t0"] + 1.0)      # 曹操改了命令
    t_gai = at("改", s4["t0"])
    t_mei = at("没", s4["t0"])            # 没过多久
    t_gei = at("给", s6["t0"])            # 给条活路
    t_jiu = at("就", t_gei)
    end = round(s6["t1"] + 1.3, 2)        # 答案落下后停 1.3s，最后一帧停在答案上

    s3_hits = [round(s3["t0"] + 0.45 + i * (s3["t1"] - s3["t0"] - 0.75) / 4, 2) for i in range(5)]
    T = {
        "end": end,
        "q_glint": at("留"),
        "q_out": round(s2["t0"] - 0.08, 2),
        "hud_in": at("湖", s2["t0"]) if any(w.startswith("湖") for _, _, w in W) else at("壶", s2["t0"]),
        "slips_in": at("下", s2["t0"]),
        "rally": t_cheng,
        "hits": s3_hits,
        "month1": t_da,
        "month2": round(t_da + 0.95, 2),
        "slips_strike": round(t_gai - 0.05, 2),
        "slips_out": round(t_gai + 0.45, 2),
        "gap": round(t_gai + 0.5, 2),
        "loosen": round(t_mei - 0.2, 2),
        "freeze": s5["t0"],
        "hud_out": s5["t0"],
        "gate_flash": [round(s5["t0"] + 0.5, 2), round(s5["t0"] + 1.35, 2)],
        "path_in": round(s6["t0"] - 0.1, 2),
        "answer": s6["t0"],
        "answer_l2": round(t_gei - s6["t0"], 2),
        "answer_src": round(t_jiu - s6["t0"], 2),
        "subs": [
            {"t0": s2["t0"], "t1": round(t_cheng - 0.06, 2), "text": "一千八百多年前，|曹操围攻壶关，下了一道命令"},
            {"t0": round(t_cheng - 0.04, 2), "t1": s2["t1"], "text": "城破之后，**全部活埋**"},
            {"t0": s3["t0"], "t1": round(t_da - 0.06, 2), "text": "结果城里的人，**个个拼命**"},
            {"t0": round(t_da - 0.04, 2), "t1": s3["t1"], "text": "打了几个月，就是打不下来"},
            {"t0": s4["t0"], "t1": round(t_cao - 0.06, 2), "text": "他的堂弟曹仁劝了**一句**"},
            {"t0": round(t_cao - 0.04, 2), "t1": round(t_mei - 0.06, 2), "text": "曹操改了命令"},
            {"t0": round(t_mei - 0.04, 2), "t1": s4["t1"], "text": "没过多久，城就降了"},
            {"t0": s5["t0"], "t1": round(s6["t0"] - 0.14, 2), "text": "曹仁劝的，是什么？", "size": 72},
        ],
    }
    json.dump(T, open(out, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(T, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
