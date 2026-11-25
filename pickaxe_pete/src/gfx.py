"""Original pixel font + sprites + drawing helpers for Pickaxe Pete. All art is drawn here in code."""
import numpy as np

# ---------------------------------------------------------------- pixel font (original 5x7 + descenders)
_G = {}
def _g(ch, *rows):
    rows = list(rows)
    while len(rows) < 9:
        rows.append("." * len(rows[0]))
    _G[ch] = np.array([[c == "#" for c in r] for r in rows], dtype=bool)

_g("A", ".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#")
_g("B", "####.", "#...#", "#...#", "####.", "#...#", "#...#", "####.")
_g("C", ".###.", "#...#", "#....", "#....", "#....", "#...#", ".###.")
_g("D", "####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####.")
_g("E", "#####", "#....", "#....", "####.", "#....", "#....", "#####")
_g("F", "#####", "#....", "#....", "####.", "#....", "#....", "#....")
_g("G", ".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####")
_g("H", "#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#")
_g("I", "###", ".#.", ".#.", ".#.", ".#.", ".#.", "###")
_g("J", "..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##..")
_g("K", "#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#")
_g("L", "#....", "#....", "#....", "#....", "#....", "#....", "#####")
_g("M", "#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#")
_g("N", "#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#")
_g("O", ".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###.")
_g("P", "####.", "#...#", "#...#", "####.", "#....", "#....", "#....")
_g("Q", ".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#")
_g("R", "####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#")
_g("S", ".####", "#....", "#....", ".###.", "....#", "....#", "####.")
_g("T", "#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#..")
_g("U", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###.")
_g("V", "#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#..")
_g("W", "#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#.")
_g("X", "#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#")
_g("Y", "#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..")
_g("Z", "#####", "....#", "...#.", "..#..", ".#...", "#....", "#####")
_g("a", ".....", ".....", ".###.", "....#", ".####", "#...#", ".####")
_g("b", "#....", "#....", "####.", "#...#", "#...#", "#...#", "####.")
_g("c", ".....", ".....", ".###.", "#....", "#....", "#....", ".###.")
_g("d", "....#", "....#", ".####", "#...#", "#...#", "#...#", ".####")
_g("e", ".....", ".....", ".###.", "#...#", "#####", "#....", ".###.")
_g("f", "..##", ".#..", "####", ".#..", ".#..", ".#..", ".#..")
_g("g", ".....", ".....", ".####", "#...#", "#...#", "#...#", ".####", "....#", ".###.")
_g("h", "#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#")
_g("i", "#", ".", "#", "#", "#", "#", "#")
_g("j", "..#", "...", "..#", "..#", "..#", "..#", "..#", "#.#", ".#.")
_g("k", "#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#")
_g("l", "#.", "#.", "#.", "#.", "#.", "#.", ".#")
_g("m", ".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#")
_g("n", ".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#")
_g("o", ".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###.")
_g("p", ".....", ".....", "####.", "#...#", "#...#", "#...#", "####.", "#....", "#....")
_g("q", ".....", ".....", ".####", "#...#", "#...#", "#...#", ".####", "....#", "....#")
_g("r", "....", "....", "#.##", "##..", "#...", "#...", "#...")
_g("s", ".....", ".....", ".####", "#....", ".###.", "....#", "####.")
_g("t", ".#..", ".#..", "####", ".#..", ".#..", ".#..", "..##")
_g("u", ".....", ".....", "#...#", "#...#", "#...#", "#...#", ".####")
_g("v", ".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#..")
_g("w", ".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#.")
_g("x", ".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#")
_g("y", ".....", ".....", "#...#", "#...#", "#...#", "#...#", ".####", "....#", ".###.")
_g("z", ".....", ".....", "#####", "...#.", "..#..", ".#...", "#####")
_g("0", ".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###.")
_g("1", ".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###")
_g("2", ".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####")
_g("3", "####.", "....#", "....#", ".###.", "....#", "....#", "####.")
_g("4", "...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#.")
_g("5", "#####", "#....", "####.", "....#", "....#", "#...#", ".###.")
_g("6", ".###.", "#....", "#....", "####.", "#...#", "#...#", ".###.")
_g("7", "#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#...")
_g("8", ".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###.")
_g("9", ".###.", "#...#", "#...#", ".####", "....#", "....#", ".###.")
_g(".", ".", ".", ".", ".", ".", ".", "#")
_g(",", "..", "..", "..", "..", "..", "..", ".#", "#.")
_g("!", "#", "#", "#", "#", "#", ".", "#")
_g("?", ".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#..")
_g("'", "#", "#", ".", ".", ".", ".", ".")
_g('"', "#.#", "#.#", "...", "...", "...", "...", "...")
_g("-", "....", "....", "....", "####", "....", "....", "....")
_g(":", ".", ".", "#", ".", ".", ".", "#")
_g(";", "..", "..", ".#", "..", "..", "..", ".#", "#.")
_g("+", ".....", "..#..", "..#..", "#####", "..#..", "..#..", ".....")
_g("=", "....", "....", "####", "....", "####", "....", "....")
_g("/", "....#", "....#", "...#.", "..#..", ".#...", "#....", "#....")
_g("(", "..#", ".#.", "#..", "#..", "#..", ".#.", "..#")
_g(")", "#..", ".#.", "..#", "..#", "..#", ".#.", "#..")
_g("^", "..#..", ".###.", "#.#.#", "..#..", "..#..", "..#..", "..#..")
_g(">", "#...", ".#..", "..#.", "...#", "..#.", ".#..", "#...")
_g("<", "...#", "..#.", ".#..", "#...", ".#..", "..#.", "...#")
_g("x", ".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#")
_g("*", ".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", ".....")
_g(" ", "...", "...", "...", "...", "...", "...", "...")
_g("%", "##..#", "##..#", "...#.", "..#..", ".#...", "#..##", "#..##")
_g("~", ".....", ".....", ".##.#", "#.##.", ".....", ".....", ".....")


def _norm(s):
    return s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("…", "...")


def text_mask(s, spacing=1):
    """Boolean mask (9 rows) of a single line at glyph-pixel scale."""
    s = _norm(s)
    cols = []
    for i, ch in enumerate(s):
        g = _G.get(ch, _G.get(ch.upper(), _G["?"]))
        cols.append(g)
        if i != len(s) - 1:
            cols.append(np.zeros((9, spacing), bool))
    if not cols:
        return np.zeros((9, 1), bool)
    return np.concatenate(cols, axis=1)


def text_width(s, scale=1, spacing=1):
    return text_mask(s, spacing).shape[1] * scale


def wrap(s, max_chars_px, scale):
    words = _norm(s).split(" ")
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_width(t, scale) <= max_chars_px or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_text(img, s, x, y, scale, color, outline=(16, 10, 26), outline_px=None, shadow=True, alpha=1.0):
    """Draw text into an HxWx3 uint8 array. x,y top-left. Outline drawn at glyph-pixel granularity."""
    m = text_mask(s)
    if outline is not None:
        mm = np.pad(m, 1)
        o = np.zeros_like(mm)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                o |= np.roll(np.roll(mm, dy, 0), dx, 1)
        if shadow:
            o |= np.roll(np.roll(mm, 2, 0), 1, 1) | np.roll(np.roll(mm, 2, 0), 0, 1) | np.roll(np.roll(mm, 2, 0), -1, 1)
        stamp(img, o, x - scale, y - scale, scale, outline, alpha)
    stamp(img, m, x, y, scale, color, alpha)
    return m.shape[1] * scale


def stamp(img, mask, x, y, scale, color, alpha=1.0):
    big = np.repeat(np.repeat(mask, scale, 0), scale, 1)
    H, W = img.shape[:2]
    h, w = big.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = big[y0 - y:y1 - y, x0 - x:x1 - x]
    reg = img[y0:y1, x0:x1]
    c = np.array(color, dtype=np.float32)
    if alpha >= 1.0:
        reg[sub] = c.astype(np.uint8)
    else:
        reg[sub] = (reg[sub] * (1 - alpha) + c * alpha).astype(np.uint8)


def draw_text_centered(img, s, cx, y, scale, color, **kw):
    w = text_width(s, scale)
    return draw_text(img, s, int(cx - w / 2), y, scale, color, **kw)


# ---------------------------------------------------------------- sprites
OUT = (22, 14, 30)
PAL = {
    "h": (205, 170, 105), "H": (120, 78, 44), "s": (242, 184, 136), "S": (205, 135, 95), "n": (226, 150, 112),
    "N": (190, 115, 85), "e": (24, 14, 30), "w": (236, 236, 228), "g": (176, 176, 172), "r": (206, 52, 52),
    "R": (146, 32, 44), "b": (96, 58, 30), "j": (64, 96, 178), "J": (42, 62, 124), "o": (104, 64, 34),
    "O": (66, 38, 22), "m": (110, 22, 34),
    # mule
    "c": (138, 116, 100), "C": (102, 84, 74), "u": (52, 40, 36), "i": (214, 146, 150), "M": (70, 54, 50),
    "z": (220, 206, 190),
    # zoe
    "G": (34, 34, 44), "a": (52, 34, 70), "p": (122, 74, 214), "P": (88, 50, 166), "d": (44, 48, 80),
    "W": (180, 180, 196), "L": (120, 230, 60), "l": (60, 150, 40), "Q": (60, 232, 255), "t": (186, 124, 86),
    "T": (150, 92, 62), "E": (255, 255, 255),
    # metal
    "k": (128, 134, 150), "K": (80, 84, 100), "y": (250, 210, 70), "Y": (200, 150, 30), "x": (176, 182, 196),
}


def sprite(rows, outline=True, pal=None):
    pal = pal or PAL
    h = len(rows)
    w = max(len(r) for r in rows)
    rgba = np.zeros((h, w, 4), np.uint8)
    for yy, r in enumerate(rows):
        for xx, ch in enumerate(r):
            if ch != "." and ch != " ":
                rgba[yy, xx, :3] = pal[ch]
                rgba[yy, xx, 3] = 255
    if outline:
        rgba = add_outline(rgba)
    return rgba


def add_outline(rgba, color=OUT):
    a = np.pad(rgba[..., 3] > 0, 1)
    rgba = np.pad(rgba, ((1, 1), (1, 1), (0, 0)))
    o = np.zeros_like(a)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        o |= np.roll(np.roll(a, dy, 0), dx, 1)
    o &= ~a
    rgba[o, :3] = color
    rgba[o, 3] = 255
    return rgba


def flip(rgba):
    return rgba[:, ::-1].copy()


def blit(img, spr, x, y, scale=1, alpha=1.0, tint=None):
    """Alpha-blit RGBA sprite onto HxWx3 image at integer pos (top-left)."""
    if scale != 1:
        spr = np.repeat(np.repeat(spr, scale, 0), scale, 1)
    x, y = int(round(x)), int(round(y))
    H, W = img.shape[:2]
    h, w = spr.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    m = s[..., 3:4].astype(np.float32) / 255.0 * alpha
    col = s[..., :3].astype(np.float32)
    if tint is not None:
        col = col * (1 - tint[3]) + np.array(tint[:3], np.float32) * tint[3]
    reg = img[y0:y1, x0:x1].astype(np.float32)
    img[y0:y1, x0:x1] = (reg * (1 - m) + col * m).astype(np.uint8)


def rotate_sprite(spr, deg):
    from PIL import Image
    im = Image.fromarray(spr, "RGBA").rotate(deg, resample=Image.NEAREST, expand=True)
    return np.array(im)


# ---- Pete (faces right)
PETE_BASE = [
    ".......hhhhhh.......",
    "......hhhhhhhh......",
    "......hhhhHhhh......",
    "......HHHHHHHH......",
    "..hhhhhhhhhhhhhhhh..",
    ".hhhhhhhhhhhhhhhhhh.",
    "......ssssssssS.....",
    ".....ssssssseSss....",
    ".....SsssssssssnN...",
    ".....wwsssssssnnN...",
    "....wwwwwwwwwwwwww..",
    "....wwwwwwwwwwwwww..",
    "...rwwwwwwgwwwwwwr..",
    "..rrwwwwwwwwwwwwwrr.",
    "..rrbwwwwgwwwwwwbrr.",
    "..rrbwwwwwwwwgwwbrr.",
    "..rrbrwwwwwwwwwrbrr.",
    "..rrbrrwwwgwwwrrbrr.",
    "..rrbrrrwwwwwrrrbrr.",
    "..ssbrrrrwwwrrrrbss.",
    "..ssbrrrrrwrrrrrbss.",
    "....bbbbbbbbbbbbb...",
    "....jjjjjjjjjjjjj...",
    "....jjjjjjjjjjjjj...",
    "....jjjjjjJjjjjjj...",
    "....jjjjjJ.Jjjjjj...",
    "....jjjjjJ.Jjjjjj...",
    "....jjjjj...jjjjj...",
    "....jjjjj...jjjjj...",
    "....JJJJJ...JJJJJ...",
    "...ooooo....oooooo..",
    "...OOOOO....OOOOOO..",
]


def _edit(rows, edits):
    rows = [list(r) for r in rows]
    for (yy, xx, ch) in edits:
        rows[yy][xx] = ch
    return ["".join(r) for r in rows]


def pete_frames():
    base = PETE_BASE
    talk1 = _edit(base, [(10, 10, "m"), (10, 11, "m"), (10, 12, "m")])
    talk2 = _edit(base, [(10, 9, "m"), (10, 10, "m"), (10, 11, "m"), (10, 12, "m"), (11, 10, "m"), (11, 11, "m"), (11, 12, "m")])
    # arms raised (for pickaxe / celebrating): hands move up near head
    up = _edit(base, [(19, 2, "r"), (19, 3, "r"), (20, 2, "r"), (20, 3, "r"), (19, 17, "r"), (19, 18, "r"), (20, 17, "r"), (20, 18, "r")])
    blink = _edit(base, [(7, 12, "s"), (7, 13, "S")])
    surprised = _edit(base, [(7, 12, "E"), (7, 13, "e"), (6, 12, "e"), (6, 13, "e"), (10, 10, "m"), (10, 11, "m"), (11, 10, "m"), (11, 11, "m"), (12, 10, "m"), (12, 11, "m")])
    return {k: sprite(v) for k, v in dict(idle=base, talk1=talk1, talk2=talk2, up=up, blink=blink, surprised=surprised).items()}


PICKAXE = sprite([
    "..xxxx........",
    ".xkkkkxx......",
    "xk....kkxx....",
    "x.......bkx...",
    "........bb.k..",
    ".......bb...k.",
    "......bb.....k",
    ".....bb.......",
    "....bb........",
    "...bb.........",
    "..bb..........",
    ".bb...........",
    "bb............",
])

# ---- Biscuit the mule (faces right)
MULE_BASE = [
    "....................cc.cc...",
    "....................ci.ci...",
    "....................ci.ci...",
    "....................cc.cc...",
    "...................Mccccc...",
    "..................MMcccecc..",
    ".................MMccccccz..",
    "................MMcccccczzz.",
    "...............MMccc.czzzzz.",
    "..cccccccccccccMccc...zzzz..",
    "Mccccccccccccccccc..........",
    "MCcccccccccccccccc..........",
    "MCcccccccccccccccc..........",
    "M.czzzzzzzzzzzzzcc..........",
    "..Cccccccccccccc.C..........",
    "..cc.cc......cc.cc..........",
    "..cc.cc......cc.cc..........",
    "..cc.cc......cc.cc..........",
    "..cc.cc......cc.cc..........",
    "..uu.uu......uu.uu..........",
]


def mule_frames():
    base = MULE_BASE
    sad = _edit(base, [(5, 23, "c"), (5, 22, "e"), (4, 22, "C"), (0, 20, "."), (0, 21, "."), (0, 23, "."), (0, 24, "."), (1, 20, "."), (1, 21, "."), (1, 23, "."), (1, 24, ".")])
    hee = _edit(base, [(9, 23, "m"), (9, 24, "m"), (9, 25, "m"), (8, 26, "E"), (9, 26, "."), (8, 25, "E")])
    blink = _edit(base, [(5, 23, "C")])
    return {k: sprite(v) for k, v in dict(idle=base, sad=sad, hee=hee, blink=blink).items()}


# ---- Zoe (faces right)
ZOE_BASE = [
    ".....GGGGGG.......",
    "....GaaaaaaG......",
    "...Gaaaaaaaaa.....",
    "...aaaaaaaaaaa....",
    "..GGaaattttttaa...",
    "..GGaatttteteta...",
    "..GGaattttttttt...",
    "...aaattttttttt...",
    "...aa.Qtttttt.....",
    "......Qttttt......",
    ".....ppppppppp....",
    "....ppppppppppp...",
    "...ppppppPpppppp..",
    "...ppppppPppppppp.",
    "..pppppppPppppp.p.",
    "..pp.ppppPppppptt.",
    "..pp.ppppppppppLLL",
    "..pp.ppppppppplLlL",
    "..tt.ppppppppplLlL",
    ".....ppppppppp.LLL",
    ".....PPPPPPPPP....",
    ".....ddddddddd....",
    ".....ddddddddd....",
    ".....dddd.dddd....",
    ".....dddd.dddd....",
    ".....dddd.dddd....",
    ".....dddd.dddd....",
    ".....dddd.dddd....",
    ".....dddd.dddd....",
    "....WWWWW.WWWWW...",
    "....EEEEE.EEEEE...",
]


def zoe_frames():
    base = ZOE_BASE
    # half-lidded deadpan eyes (lids drawn in skin shade)
    base = _edit(base, [(4, 9, "T"), (4, 11, "T")])
    talk1 = _edit(base, [(7, 10, "m"), (7, 11, "m")])
    talk2 = _edit(base, [(7, 10, "m"), (7, 11, "m"), (8, 10, "m"), (8, 11, "m")])
    smile = _edit(base, [(7, 9, "m"), (7, 10, "m"), (7, 11, "m"), (6, 12, "m")])
    blink = _edit(base, [(5, 9, "t"), (5, 11, "t")])
    return {k: sprite(v) for k, v in dict(idle=base, talk1=talk1, talk2=talk2, smile=smile, blink=blink).items()}


COIN_FRAMES = [sprite(r) for r in (
    [".yyyy.", "yyYYyy", "yYyyYy", "yYyyYy", "yyYYyy", ".yyyy."],
    ["..yy..", ".yYYy.", ".yYyy.", ".yYyy.", ".yYYy.", "..yy.."],
    ["..y...", "..Y...", "..Y...", "..Y...", "..Y...", "..y..."],
    ["..yy..", ".yYYy.", ".yyYy.", ".yyYy.", ".yYYy.", "..yy.."],
)]

SPARKLE = [sprite(r, outline=False, pal={"E": (255, 255, 255), "y": (255, 240, 120)}) for r in (
    ["..E..", ".yEy.", "EEEEE", ".yEy.", "..E.."],
    [".....", "..E..", ".EEE.", "..E..", "....."],
)]

MINECART = sprite([
    "kkkkkkkkkkkkkkkkkkkkkkkk",
    "kKKKKKKKKKKKKKKKKKKKKKKk",
    ".kHHHHHHHHHHHHHHHHHHHHk.",
    ".kHoHHHHHHoHHHHHHHHoHHk.",
    ".kHHHHHHHHHHHHHHHHHHHHk.",
    "..kHHHHHHHHHHHHHHHHHHk..",
    "..kkkkkkkkkkkkkkkkkkkk..",
    "...KKK............KKK...",
    "..KkkkK..........KkkkK..",
    "...KKK............KKK...",
])

# ---- dragon (faces left), two wing frames. body = server metal with LED stripe
_DR_PAL = dict(PAL)
_DR_PAL.update({"d": (60, 170, 120), "D": (34, 110, 84), "f": (255, 120, 40), "F": (255, 220, 80), "v": (120, 255, 170), "r": (230, 50, 60)})
DRAGON = [sprite(r, pal=_DR_PAL) for r in (
    [
        "...........DD.............DD.",
        "..........DddD...........Dd..",
        ".........DdddD.........DDd...",
        "........DddddD.......DDdd....",
        ".......DdddddD.....DDddd.....",
        "..ddd..DddddddDDDDDdddd......",
        ".ddrdd..DddddddddddddD.......",
        "dddddddDddddddddddddd........",
        ".vvdddddvdvdvdvdvddddd.......",
        "..dddddddddddddddddddddd.....",
        "...dd..ddddddddddddd..dddd...",
        ".......dd..dd...dd.dd...ddd..",
        ".......DD..DD...DD.DD.....dd.",
    ],
    [
        ".............................",
        ".............................",
        ".............................",
        ".............................",
        "..ddd........................",
        ".ddrdd.......................",
        "dddddddDddddddddddddd........",
        ".vvdddddvdvdvdvdvddddddd.....",
        "..dddddddddddddddddddddddd...",
        "...dd..DddddddddddddD.dddd...",
        ".......DdddddDDDDDdddD..ddd..",
        "........DdddD......DddD...dd.",
        ".........DDD........DDD......",
    ],
)]


def rack_sprite(w=14, h=20):
    """Small server rack (for crowds). Returns RGBA with LED slots left transparent-colored for animation."""
    a = np.zeros((h, w, 4), np.uint8)
    a[..., :3] = PAL["K"]
    a[..., 3] = 255
    a[1:-1, 1:-1, :3] = (46, 50, 64)
    for yy in range(2, h - 2, 3):
        a[yy:yy + 2, 2:-2, :3] = (70, 76, 96)
    return add_outline(a)


# ---------------------------------------------------------------- misc helpers
def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t):
    t = clamp(t)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0


def dither_gradient(h, w, stops, y0=0, total=None):
    """Vertical banded gradient with ordered dithering (retro look). stops: list of (pos0..1, rgb)."""
    total = total or h
    ys = (np.arange(h) + y0) / max(1, total - 1)
    pos = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], np.float32)
    nb = len(stops)
    # quantise into bands, dither between neighbouring stops
    img = np.zeros((h, w, 3), np.uint8)
    th = np.tile(BAYER4, (h // 4 + 2, w // 4 + 2))[:h, :w]
    for yy in range(h):
        y = ys[yy]
        i = np.searchsorted(pos, y) - 1
        i = int(np.clip(i, 0, nb - 2))
        f = (y - pos[i]) / max(1e-6, pos[i + 1] - pos[i])
        f = np.clip(f, 0, 1)
        row = np.where(th[yy] < f, 1, 0)
        img[yy] = np.where(row[:, None] == 1, cols[i + 1], cols[i]).astype(np.uint8)
    return img


def rect(img, x, y, w, h, color, alpha=1.0):
    x, y, w, h = int(x), int(y), int(w), int(h)
    H, W = img.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    if alpha >= 1:
        img[y0:y1, x0:x1] = color
    else:
        img[y0:y1, x0:x1] = (img[y0:y1, x0:x1] * (1 - alpha) + np.array(color) * alpha).astype(np.uint8)


def circle(img, cx, cy, r, color, alpha=1.0):
    H, W = img.shape[:2]
    x0, x1 = int(max(0, cx - r - 1)), int(min(W, cx + r + 2))
    y0, y1 = int(max(0, cy - r - 1)), int(min(H, cy + r + 2))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    m = (xx - cx + 0.5) ** 2 + (yy - cy + 0.5) ** 2 <= r * r
    reg = img[y0:y1, x0:x1]
    if alpha >= 1:
        reg[m] = color
    else:
        reg[m] = (reg[m] * (1 - alpha) + np.array(color) * alpha).astype(np.uint8)


def ring(img, cx, cy, r0, r1, color):
    H, W = img.shape[:2]
    x0, x1 = int(max(0, cx - r1 - 1)), int(min(W, cx + r1 + 2))
    y0, y1 = int(max(0, cy - r1 - 1)), int(min(H, cy + r1 + 2))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = (xx - cx + 0.5) ** 2 + (yy - cy + 0.5) ** 2
    m = (d <= r1 * r1) & (d >= r0 * r0)
    img[y0:y1, x0:x1][m] = color


def line(img, x0, y0, x1, y1, color):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    H, W = img.shape[:2]
    for i in range(n):
        t = i / max(1, n - 1)
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        if 0 <= x < W and 0 <= y < H:
            img[y, x] = color


class Canvas:
    """Transparent RGBA scratch canvas: compose a character at 1x, then blit scaled (keeps pixel grid consistent)."""

    def __init__(self, w, h, ox, oy):
        self.a = np.zeros((h, w, 4), np.uint8)
        self.ox, self.oy = ox, oy

    def put(self, spr, x, y):
        x, y = int(round(x + self.ox)), int(round(y + self.oy))
        H, W = self.a.shape[:2]
        h, w = spr.shape[:2]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
        m = s[..., 3] > 0
        self.a[y0:y1, x0:x1][m] = s[m]

    def rect(self, x, y, w, h, c):
        x, y = int(round(x + self.ox)), int(round(y + self.oy))
        self.a[max(0, y):max(0, y + h), max(0, x):max(0, x + w)] = (*c, 255)

    def blit_to(self, img, x, y, scale=1):
        """x,y = position of canvas origin (0,0 in character coords) in img."""
        blit(img, self.a, x - self.ox * scale, y - self.oy * scale, scale)


def safe_px(img, x, y, c):
    H, W = img.shape[:2]
    x, y = int(x), int(y)
    if 0 <= x < W and 0 <= y < H:
        img[y, x] = c


KEY = (255, 0, 254)


def offscreen(w, h):
    b = np.zeros((h, w, 3), np.uint8)
    b[:] = KEY
    return b


def key_to_rgba(buf):
    a = np.zeros(buf.shape[:2] + (4,), np.uint8)
    a[..., :3] = buf
    a[..., 3] = np.where(np.all(buf == KEY, axis=-1), 0, 255)
    return a
