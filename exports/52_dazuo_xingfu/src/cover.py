import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from art import *
import scenes as SC
D = os.path.dirname(os.path.abspath(__file__))

def cover():
    im = SC.courtyard_static().copy()
    bam = bamboo(seed=7, n=6)
    a = bam.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.28))
    sh = Image.new("RGBA", (W, H), (40, 36, 30, 0)); sh.putalpha(a)
    im.alpha_composite(sh.transform((W, H), Image.AFFINE, (1, 0.35, -420, 0, 1, -60)))
    im.alpha_composite(bam)
    fig = figure(1.1)
    im.alpha_composite(fig, (int(W * 0.36 - fig.width / 2), 1390 - fig.height))
    # title block on soft paper band
    band = Image.new("RGBA", (W, 470), PAPER + (0,))
    al = np.zeros((470, W), np.float32); yy = np.arange(470)[:, None]
    al[:] = 215 * np.clip(np.minimum(yy / 60, (470 - yy) / 60), 0, 1)
    band.putalpha(Image.fromarray(al.astype(np.uint8)))
    im.alpha_composite(band, (0, 170))
    paste_c(im, text_img("打坐让人幸福", "black", 128, INK), 540, 330)
    paste_c(im, text_img("证据到底有多硬？", "black", 104, RED), 540, 480)
    paste_c(im, text_img("走神研究 · 47 项随机试验 · 慈心禅 · 坛经印照", "kai", 42, INK2), 540, 590)
    s = seal("静坐的科学", 200, seed=171, rot=-4)
    paste_c(im, s, 860, 1180)
    paste_c(im, text_img("印照，不是证明", "kai", 56, INK), 540, 1470)
    paste_c(im, text_img("AI 配音 · 画面示意", "serif_r", 28, GREY), 540, 1850)
    return im.convert("RGB")

c = cover()
c.save(f"{D}/cover_9x16.png")
c.crop((0, 140, 1080, 1580)).save(f"{D}/cover_3x4.png")
print("ok")
