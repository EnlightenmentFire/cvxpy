"""Lay the script out in time and answer 'what is on screen at time t'."""
import json
import math
import os
import re

from gfx import theme, blend_theme, ease, ease_out, clamp
from wheel import WheelState, ORDER_KE, ORDER_SHENG, KE_TEXT, SHENG_TEXT, sector_angle

SEG_NUM = {"S1": "一", "S2": "二", "S3": "三", "S4": "四", "S5": "五", "S6": "六", "S7": "七",
           "S8": "八", "S9": "九"}
GAP_LINE = 0.30
GAP_QUOTE = 0.38
GAP_SEG = 1.35
LEAD_IN = 0.6

SHENG_LABELS = {"木": "伏羲 · 周", "火": "神农 · 尧 · 汉", "土": "黄帝 · 舜", "金": "少昊 · 禹",
                "水": "颛顼 · 汤"}
DEMO_KEYS = {"ke": ["破土", "伐木", "熔金", "灭火", "挡水"]}


def han_len(s):
    return len([c for c in s if "一" <= c <= "鿿"])


def estimate_duration(line):
    n = han_len(line["text"])
    return n / (3.9 if line["kind"] == "Q" else 4.7) + 0.25


class Timeline:
    def __init__(self, segs, durations=None):
        self.segs = segs
        self.lines = []
        t = LEAD_IN
        for si, seg in enumerate(segs):
            if si > 0:
                t += GAP_SEG
            seg["t0"] = t
            for ln in seg["lines"]:
                for c in ln["cues"]:
                    if c["cmd"] == "pause":
                        t += float(c.get("s", 0.5))
                d = (durations or {}).get(ln["id"]) or estimate_duration(ln)
                ln["t0"], ln["t1"] = t, t + d
                ln["dur"] = d
                self.lines.append(ln)
                t = ln["t1"] + (GAP_QUOTE if ln["kind"] == "Q" else GAP_LINE)
            seg["t1"] = t
        tail = sum(float(c.get("s", 0.5)) for c in self.lines[-1].get("cues_end", []) if c["cmd"] == "pause")
        self.total = t + 0.5 + tail
        self._build_events()

    # ------------------------------------------------------------ events
    def _build_events(self):
        self.theme_keys = []      # (t, theme_name, fade)
        self.stage_keys = []      # (t, name, seg_id)
        self.fx = []              # (t, name, params)
        self.notes = []           # (t0, t1, text)
        self.sfx = []             # (t, name)
        self.wheel_cues = []      # (t, cue, line)
        for seg in self.segs:
            self.theme_keys.append((seg["t0"] - 0.6, seg["theme"], 1.4))
            for ln in seg["lines"]:
                pre = sum(float(c.get("s", 0.5)) for c in ln["cues"] if c["cmd"] == "pause")
                tc = ln["t0"] - pre
                for c in ln["cues"]:
                    if c["cmd"] == "pause":
                        tc += float(c.get("s", 0.5))
                        continue
                    self._cue(c, tc, ln)
                for c in ln.get("cues_end", []):
                    self._cue(c, ln["t1"], ln)
        self.theme_keys.sort(key=lambda x: x[0])
        self.stage_keys.sort(key=lambda x: x[0])
        self.fx.sort(key=lambda x: x[0])
        self._build_wheel()

    def _cue(self, c, t, ln):
        cmd = c["cmd"]
        if cmd == "stage":
            self.stage_keys.append((t - 0.25, c["_args"][0], ln["seg"]))
        elif cmd == "theme":
            self.theme_keys.append((t, c["_args"][0], 1.6))
        elif cmd == "fx":
            self.fx.append((t, c["_args"][0], dict(c)))
        elif cmd == "sfx":
            self.sfx.append((t, c["_args"][0]))
        elif cmd == "note":
            text = c.get("text", "")
            self.notes.append((t, min(ln["t1"] + 2.5, t + 9.0), text))
        elif cmd == "wheel":
            self.wheel_cues.append((t, c, ln))

    def _build_wheel(self):
        """Pre-compute wheel keyframes from cues."""
        self.wk_mode = [(0.0, "hidden")]
        self.wk_go = []        # (t, el, label, from_angle, to_angle)
        self.wk_flip = None
        self.wk_demo = []      # (t_appear, e0, e1, text)
        self.wk_ghost = []     # (t, el)
        self.wk_q = []         # (t0, t1)
        self.wk_spin = None
        labels_init = {"火": "周"}
        angle = sector_angle(3)
        order = list(ORDER_KE)
        cur_el = "火"
        for (t, c, ln) in sorted(self.wheel_cues, key=lambda x: x[0]):
            if "mode" in c:
                self.wk_mode.append((t, c["mode"]))
            if "go" in c:
                el = c["go"]
                if self.wk_flip and t > self.wk_flip[0]:
                    order = list(ORDER_SHENG)
                target = sector_angle(order.index(el))
                d = (target - angle + 540) % 360 - 180
                self.wk_go.append((t + 0.15, el, c.get("label"), angle, angle + d))
                angle += d
                cur_el = el
            if "_args" in c and "demo" in c["_args"]:
                n = len(ln["text"])
                for k, key in enumerate(DEMO_KEYS["ke"]):
                    pos = ln["text"].find(key)
                    frac = (pos + len(key)) / n if pos >= 0 else (k + 1) / 6
                    e0, e1 = ORDER_KE[k], ORDER_KE[(k + 1) % 5]
                    self.wk_demo.append((ln["t0"] + frac * ln["dur"] - 0.25, e0, e1, KE_TEXT[(e0, e1)]))
            if "_args" in c and "flip" in c["_args"]:
                self.wk_flip = (t, 2.4)
                order = list(ORDER_SHENG)
                target = sector_angle(order.index("火"))
                self.wk_flip_angles = (angle, target)
                angle = target
                cur_el = "火"
            if "ghost" in c:
                self.wk_ghost.append((t, c["ghost"]))
            if "_args" in c and "q" in c["_args"]:
                self.wk_q.append((t, ln["t1"] + 1.5))
            if "_args" in c and "spin" in c["_args"]:
                self.wk_spin = (t, 7.0)
        self.labels_init = labels_init
        # wheel size follows the stage: big on the wheel stages, mini elsewhere
        first_vis = next((t for (t, m) in self.wk_mode if m != "hidden"), None)
        modes = [(0.0, "hidden")]
        if first_vis is not None:
            modes.append((first_vis, "mini"))
            for (tk, name, seg) in self.stage_keys:
                if tk < first_vis:
                    continue
                if name in ("wheel_stage", "run_slot"):
                    modes.append((tk, "big"))
                elif name == "end_card":
                    modes.append((tk, "hidden"))
                else:
                    modes.append((tk, "mini"))
        self.wk_mode = sorted(modes, key=lambda x: x[0])
        # run slot appears with fx run_slot (or chain_gap)
        self.t_run_slot = next((t for (t, n, p) in self.fx if n in ("chain_gap", "run_slot")), None)
        self.t_center_text = next((t for (t, n, p) in self.fx if n == "zhongshi"), None)

    # ------------------------------------------------------------ queries
    def seg_at(self, t):
        cur = self.segs[0]
        for s in self.segs:
            if t >= s["t0"] - 0.6:
                cur = s
        return cur

    def line_at(self, t):
        """Current spoken line (or the previous one during a short gap)."""
        prev = None
        for ln in self.lines:
            if ln["t0"] <= t < ln["t1"]:
                return ln, True
            if ln["t1"] <= t:
                prev = ln
        return prev, False

    def theme_at(self, t):
        base = self.theme_keys[0][1]
        for (tk, name, fade) in self.theme_keys:
            if t < tk:
                break
            if t < tk + fade:
                return blend_theme(theme(base), theme(name), ease((t - tk) / fade))
            base = name
        return theme(base)

    def stage_at(self, t):
        """Returns (name, t_start, prev_name, prev_start, crossfade_k)."""
        cur, ts, prev, pts = None, 0.0, None, 0.0
        for (tk, name, seg) in self.stage_keys:
            if t < tk:
                break
            prev, pts = cur, ts
            cur, ts = name, tk
        k = clamp((t - ts) / 0.6) if prev else 1.0
        return cur, ts, prev, pts, k

    def fx_time(self, name, t, since=None):
        """Most recent start time of fx `name` at or before t (optionally after `since`)."""
        best = None
        for (tf, n, p) in self.fx:
            if n == name and tf <= t and (since is None or tf >= since - 0.3):
                best = tf
        return best

    def fx_param(self, name, t, key, default=None):
        best = default
        for (tf, n, p) in self.fx:
            if n == name and tf <= t:
                best = p.get(key, default)
        return best

    def wheel_at(self, t):
        st = WheelState()
        # visibility / size
        mode, mt = "hidden", 0.0
        prev_mode = "hidden"
        for (tk, m) in self.wk_mode:
            if t >= tk:
                prev_mode, mode, mt = mode, m, tk
        k = ease(clamp((t - mt) / 1.0))

        def mval(m):
            return (0.0, 0.0) if m == "hidden" else ((1.0, 0.0) if m == "mini" else (1.0, 1.0))
        a0, b0 = mval(prev_mode)
        a1, b1 = mval(mode)
        st.alpha = a0 + (a1 - a0) * k
        st.big = b0 + (b1 - b0) * k
        if prev_mode == "hidden" and mode != "hidden":
            st.big = b1
        # pointer
        st.labels = dict(self.labels_init)
        st.angle = sector_angle(3)
        st.active = "火"
        order = list(ORDER_KE)
        flip_t = self.wk_flip[0] if self.wk_flip else None
        for (tg, el, lab, fa, ta) in self.wk_go:
            if flip_t is not None and flip_t <= tg and order is ORDER_KE:
                pass
            if t < tg:
                break
            p = clamp((t - tg) / 0.9)
            # damped overshoot
            pe = 1 - math.exp(-5.5 * p) * math.cos(7.0 * p) if p < 1 else 1.0
            st.angle = fa + (ta - fa) * pe
            if p > 0.55:
                st.active = el
                if lab:
                    st.labels[el] = lab
            st.pulse = max(0.0, 1 - (t - tg - 0.5) / 0.8) if t - tg > 0.5 else 0.0
        # flip
        if self.wk_flip:
            ft, fd = self.wk_flip
            if t >= ft:
                p = clamp((t - ft) / fd)
                if p < 1:
                    st.flip = p
                    st.next_order = list(ORDER_SHENG)
                if p >= 0.5:
                    st.order = list(ORDER_SHENG)
                    st.labels = dict(SHENG_LABELS)
                    # re-apply post-flip go labels
                    st.angle = self.wk_flip_angles[1]
                    st.active = "火"
                    for (tg, el, lab, fa, ta) in self.wk_go:
                        if tg <= ft or t < tg:
                            continue
                        pp = clamp((t - tg) / 0.9)
                        pe = 1 - math.exp(-5.5 * pp) * math.cos(7.0 * pp) if pp < 1 else 1.0
                        st.angle = fa + (ta - fa) * pe
                        if pp > 0.55:
                            st.active = el
                            if lab:
                                base = SHENG_LABELS.get(el, "")
                                st.labels[el] = (base + " · " + lab) if lab not in base else base
                        st.pulse = max(0.0, 1 - (t - tg - 0.5) / 0.8) if t - tg > 0.5 else 0.0
                    # 生 arrows shown right after the flip, then fade
                    ap = clamp((t - ft - fd * 0.55) / 1.0) * (1 - clamp((t - ft - fd - 9.0) / 1.5))
                    if ap > 0:
                        for i in range(5):
                            e0, e1 = ORDER_SHENG[i], ORDER_SHENG[(i + 1) % 5]
                            st.arrows.append((e0, e1, SHENG_TEXT[(e0, e1)], ap * clamp((t - ft - fd * 0.55 - i * 0.25) / 0.5)))
        # demo arrows (克)
        for (ta, e0, e1, txt) in self.wk_demo:
            if t >= ta:
                life = clamp((t - ta) / 0.4) * (1 - clamp((t - ta - 10.0) / 1.5))
                if life > 0:
                    st.arrows.append((e0, e1, txt, life))
        # ghost
        for (tg, el) in self.wk_ghost:
            if t >= tg:
                life = clamp((t - tg) / 0.4) * (1 - clamp((t - tg - 6.0) / 1.0))
                if life > 0:
                    st.ghost = (el, life * (0.65 + 0.35 * math.sin((t - tg) * 4.0)))
        # question
        for (q0, q1) in self.wk_q:
            if q0 <= t:
                st.question = clamp((t - q0) / 0.4) * (1 - clamp((t - q1) / 0.6))
        # run slot
        if self.t_run_slot is not None and t >= self.t_run_slot and st.order == ORDER_SHENG:
            st.run_slot = ease(clamp((t - self.t_run_slot) / 1.2))
        # spin
        if self.wk_spin:
            s0, sd = self.wk_spin
            if t >= s0:
                p = clamp((t - s0) / sd)
                # accelerate then decelerate; total 3 turns
                st.spin = 360 * 3 * (p * p * (3 - 2 * p))
        if self.t_center_text is not None and t >= self.t_center_text:
            st.center_text = ease(clamp((t - self.t_center_text) / 1.5))
        return st

    def notes_at(self, t):
        out = []
        for (a, b, text) in self.notes:
            if a <= t <= b:
                out.append((text, clamp((t - a) / 0.4) * (1 - clamp((t - b + 0.5) / 0.5))))
        return out


def load_durations(path):
    if path and os.path.exists(path):
        return json.load(open(path))
    return None
