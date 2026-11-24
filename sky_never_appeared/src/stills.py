"""Render the key stills for style approval."""
import os, sys
import numpy as np
import cv2
from common import *
import fx
import scene_sky as SKY
import scenes2d as S2

OUT = os.path.join(ROOT, 'stills')
os.makedirs(OUT, exist_ok=True)


def save(name, img):
    cv2.imwrite(os.path.join(OUT, name), cv2.cvtColor(to_u8(img), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print('saved', name, flush=True)
    return img


def sky_still(name, t, sub=None, mode='open', dissolve=0.0, fade_beams=0.0):
    c, e, cam = SKY.draw_sky(t, mode=mode, dissolve=dissolve, fade_beams=fade_beams)
    img = SKY.finish(c, e, int(t * 30), hypo=1.0)
    fx.hypo_overlay(img)
    if sub:
        fx.subtitle(img, sub)
    return save(name, img)


def flat_still(name, fn, sub=None, chapter=None):
    c, e = fn()
    img = S2.finish(c, e, 3)
    if chapter:
        fx.chapter_label(img, *chapter)
    if sub:
        fx.subtitle(img, sub)
    return save(name, img)


if __name__ == '__main__':
    imgs = []
    imgs.append(sky_still('01_cold_open_station.jpg', 9.95))
    imgs.append(sky_still('02_xray_burst.jpg', 12.58))
    imgs.append(flat_still('03_balance_shield.jpg', lambda: S2.balance(3.0, 'shield'),
                           '是先打你，再挡住你的还击', (2, '一面盾')))
    imgs.append(flat_still('04_letter.jpg', lambda: S2.letter(3.6),
                           '说X射线激光已经“进入工程阶段”', (3, '神剑')))
    imgs.append(flat_still('05_hoe_deception.jpg', lambda: S2.hoe(2.0, card=1.0),
                           '第四次的命中，是真撞上的', (4, '那一次命中')))
    imgs.append(flat_still('06_reykjavik_laboratory.jpg', lambda: S2.reykjavik_lab(2.2),
                           '最后卡住的，只是一个词：实验室', (6, '一个词')))
    imgs.append(flat_still('07_polyus_tumble.jpg', lambda: S2.polyus_diagram(5.8),
                           '按苏联官方事后的报告，它翻了大约两整圈', (7, '苏联的天空')))
    imgs.append(sky_still('08_ending_dissolve.jpg', 11.3, '那片天空从来没有出现',
                          mode='end', dissolve=0.42, fade_beams=0.75))
    sheet = np.concatenate([np.concatenate(imgs[:4], 1), np.concatenate(imgs[4:], 1)], 0)
    sheet = cv2.resize(sheet, (sheet.shape[1] // 3, sheet.shape[0] // 3), interpolation=cv2.INTER_AREA)
    save('00_contact_sheet.jpg', sheet)
