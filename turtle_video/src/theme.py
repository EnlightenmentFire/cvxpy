"""Palette, fonts and small math helpers shared by every scene."""
import math
import skia

W, H, FPS = 1080, 1920, 30

# ---- layout (WeChat Channels safe zones) -------------------------------------
# top ~0-220 and bottom ~1500-1920 are covered by the player UI.
STAGE_TOP, STAGE_BOT = 250, 1290
SUB_Y = 1392          # subtitle block centre
NOTE_Y = 1282         # small source-note baseline (above subtitles)
MARGIN = 72

# ---- palette ----------------------------------------------------------------
BG = (9, 24, 19)          # deep ink green
BG_HI = (17, 42, 32)
BG_LO = (5, 14, 11)
GRID = (28, 62, 48)
GOLD = (204, 166, 88)     # dark gold
GOLD_HI = (232, 200, 128)
GOLD_DIM = (124, 101, 58)
PHOS = (104, 226, 160)    # terminal phosphor green
PHOS_DIM = (44, 116, 84)
CREAM = (238, 230, 208)
MUTED = (146, 158, 148)
PAPER = (229, 217, 188)
PAPER_DARK = (196, 178, 138)
NEWS = (212, 196, 152)
INK = (46, 40, 31)
INK_SOFT = (112, 100, 80)
LOSS = (204, 96, 72)
GRAY = (104, 112, 106)
SILH = (4, 10, 8)


def col(rgb, a=1.0):
    r, g, b = rgb
    return skia.Color(int(r), int(g), int(b), int(max(0, min(1, a)) * 255))


def mix(c1, c2, t):
    return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))


# ---- fonts --------------------------------------------------------------------
_ND = "/usr/share/fonts/opentype/noto/"
_TF = {}


def tf(name):
    if name not in _TF:
        spec = {
            "black": (_ND + "NotoSansCJK-Black.ttc", 2),
            "bold": (_ND + "NotoSansCJK-Bold.ttc", 2),
            "medium": (_ND + "NotoSansCJK-Medium.ttc", 2),
            "regular": (_ND + "NotoSansCJK-Regular.ttc", 2),
            "light": (_ND + "NotoSansCJK-Light.ttc", 2),
            "serif": (_ND + "NotoSerifCJK-Bold.ttc", 2),
            "serif_r": (_ND + "NotoSerifCJK-Regular.ttc", 2),
            "mono": ("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf", 0),
            "mono_r": ("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf", 0),
            "mono_x": ("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf", 0),
            "type": ("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf", 0),
            "type_r": ("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 0),
            "news": ("/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf", 0),
            "news_r": ("/usr/share/fonts/truetype/freefont/FreeSerif.ttf", 0),
        }[name]
        _TF[name] = skia.Typeface.MakeFromFile(*spec)
    return _TF[name]


_FONTS = {}


def font(name, size):
    key = (name, round(size, 1))
    if key not in _FONTS:
        f = skia.Font(tf(name), size)
        f.setSubpixel(True)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        _FONTS[key] = f
    return _FONTS[key]


# ---- easing -------------------------------------------------------------------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def ramp(t, t0, t1):
    """0 before t0, 1 after t1, smooth in between."""
    if t1 <= t0:
        return 1.0 if t >= t0 else 0.0
    return smooth((t - t0) / (t1 - t0))


def fade_window(t, t_in, t_out, dur=0.45):
    """1 inside [t_in, t_out], smooth fade of `dur` at both ends."""
    return min(ramp(t, t_in, t_in + dur), 1 - ramp(t, t_out - dur, t_out))


def osc(t, period, phase=0.0):
    return math.sin(2 * math.pi * (t / period + phase))
