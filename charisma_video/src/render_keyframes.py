# -*- coding: utf-8 -*-
import os, sys
import PIL.Image as I
from engine import *
import routemap as rm, scene_rome as sr, scene_open as so, scene_medieval as sme, scene_east as se, scene_modern as smo

OUT = sys.argv[1] if len(sys.argv) > 1 else "keyframes"
os.makedirs(OUT, exist_ok=True)

def frame(name, fn):
    s = new_surface(); c = s.getCanvas()
    fn(c)
    img = I.fromarray(surface_to_rgb(s))
    img.save(os.path.join(OUT, name + ".png"))
    return img

def k1(c):
    draw_bg(c)
    so.draw_meeting(c, look_up=1.0, line_a=1.0, zh_a=1.0, portrait_glow=0.8)
    chapter_label(c, "上世纪七十年代 · 迪士尼"); tag_badge(c, "情景示意")
    subtitle(c, "大家抬起头，看了看墙上的画像")
    footnote(c, "画面为情景示意，人物为剪影。“What would Walt do?”的说法见《好莱坞报道者》2011、卡特穆尔《创新公司》2014 等")

def k2(c):
    draw_bg(c)
    so.draw_lecture(c, 1.0); so.draw_cards(c, (1, 1, 1), 1.0)
    chapter_label(c, "人为什么服从？")
    subtitle(c, "夹在中间的第二种，最特别")
    footnote(c, "韦伯《以政治为业》：1919 年 1 月 28 日慕尼黑演讲，同年出版（印行本有扩写）")

def k3(c):
    draw_bg(c)
    chapter_label(c, "他走了以后 · 六条路")
    rm.draw_map(c, glow=1, extinguish=1, split=1, icons=1, labels=[1] * 6, costs=[1] * 6, show_center_label=1,
                active=1, travel=0.55, dim_others=0.0)
    subtitle(c, "每一条路，也都有代价")
    footnote(c, "韦伯《经济与社会》（1922）第一部分第三章 §11“魅力的日常化”，原文列为 a)–f) 六种办法")

def k4(c):
    sr.draw_coins(c, appear=1, links=1, final_link=1, crack=0.75, rust=0.65)
    chapter_label(c, "c) 前任指定 · 罗马")
    tag_badge(c, "对照例子（韦伯原文在这一条举的是古罗马官职的任命）")
    subtitle(c, "他把皇位传给了康茂德")
    footnote(c, "前四位多因没有存活的亲生儿子而收养；“五贤帝”之说可追溯到马基雅维利《论李维》I.10")

def k5(c):
    sme.draw_viterbo(c, roof_off=0.62, bread=1, letter=1.0)
    chapter_label(c, "d) 推选＋认可 · 维泰博 1268–1271")
    subtitle(c, "掀掉了屋顶，还威胁要断他们的粮")
    footnote(c, "据枢机主教们 1270 年 6 月的信（落款 in discooperto palatio）及枢机主教霍斯蒂恩西斯的记述")

def k6(c):
    se.draw_han(c)
    chapter_label(c, "e) 血统 · 汉初"); tag_badge(c, "对照例子")
    subtitle(c, "不是刘家的人封王，天下一起打他")
    footnote(c, "《史记·吕太后本纪》：“高帝刑白马盟曰‘非刘氏而王，天下共击之’。今王吕氏，非约也。”")

def k7(c):
    se.draw_ottoman(c, lamps_on=12, fading=0.5)
    chapter_label(c, "e) 血统 · 奥斯曼"); tag_badge(c, "韦伯原文提到的例子")
    subtitle(c, "1595 年，穆罕默德三世即位的那一夜")
    footnote(c, "韦伯《经济与社会》§11：die „Pflicht“ der Ausrottung aller sonst denkbaren Anwärter im Hause Osmans")

def k8(c):
    smo.draw_companies(c, ice=0.85, stage=4)
    chapter_label(c, "回到公司"); tag_badge(c, "对照例子")
    subtitle(c, "同一个问题，一家把它变成了口头禅", y=1420)
    footnote(c, "《纽约时报》2014-08-10（Brian X. Chen）；库克 2011 年追思会、2012 年 D10 大会的讲述。黑板上的公牛为本片自绘")

FRAMES = [("01_冷启动_会议室", k1), ("02_韦伯1919_三种理由", k2), ("03_六条路_路线图", k3),
          ("04_罗马钱币_前任指定", k4), ("05_维泰博_屋顶", k5), ("06_汉初_白马之盟", k6),
          ("07_奥斯曼_十九盏灯", k7), ("08_迪士尼与苹果", k8)]

if __name__ == "__main__":
    imgs = []
    for name, fn in FRAMES:
        imgs.append(frame(name, fn)); print(name, flush=True)
    # contact sheet 4x2
    tw, th = 360, 640
    sheet = I.new("RGB", (tw * 4 + 50, th * 2 + 30), (10, 10, 10))
    for i, im in enumerate(imgs):
        sheet.paste(im.resize((tw, th), I.LANCZOS), (10 + (i % 4) * (tw + 10), 10 + (i // 4) * (th + 10)))
    sheet.save(os.path.join(OUT, "00_总览.jpg"), quality=90)
