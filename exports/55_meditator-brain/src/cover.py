"""Cover images: 1080x1920 (vertical) and 1080x1440 (3:4 crop-safe)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import skia
from gfx import *
import scenes as S

def cover(h):
    surf = skia.Surface(W, h); c = surf.getCanvas()
    c.save(); c.translate(0, (h - H) / 2); S.bg_lab(c, 3.0); c.restore()
    cy = h * 0.43
    S.head_top(c, W / 2, cy, 250 if h > 1500 else 210, 3.0, lit=1, sync=1)
    S.scope(c, 70, cy + 300, W - 140, 220, 3.0, 1.0, 1.0, rows=3, col='#ffd59a')
    top = 150 if h > 1500 else 90
    text(c, '佛法与心智 · 静坐的科学', W / 2, top, 36, 'sans', '#c9b48a', 1, spacing=3)
    text(c, '修行几万小时的人', W / 2, top + 140, 104, 'serif_k', '#f6efe2', 1, shadow=('#000000', 0.8, 10, 0, 4))
    text(c, '大脑有什么不一样？', W / 2, top + 270, 104, 'serif_k', '#ffd59a', 1, shadow=('#000000', 0.8, 10, 0, 4))
    yb = cy + 600 if h > 1500 else h - 130
    chip(c, '伽马同步 · 皮层厚度 · 因果之谜', W / 2, yb, 40, '#06121c', S.CYAN, 1)
    if h > 1500:
        text(c, '印照，不是证明', W / 2, yb + 170, 56, 'serif_b', '#f6efe2', 1)
        seal(c, '印照', W / 2, yb + 290, 44, 1)
    return surf

if __name__ == '__main__':
    out = sys.argv[1]
    cover(1920).makeImageSnapshot().save(os.path.join(out, 'cover_1080x1920.png'))
    cover(1440).makeImageSnapshot().save(os.path.join(out, 'cover_1080x1440.png'))
