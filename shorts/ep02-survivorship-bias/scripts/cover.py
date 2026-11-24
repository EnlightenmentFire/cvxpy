import sys, math, cairo, numpy as np
sys.path.insert(0, __file__.rsplit('/',1)[0])
import scene as S
from PIL import Image, ImageDraw
W,H=1080,1440
surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H); ctx=cairo.Context(surf)
g=cairo.LinearGradient(0,0,0,H); g.add_color_stop_rgb(0,*S.BG_TOP); g.add_color_stop_rgb(1,*S.BG_BOT); ctx.set_source(g); ctx.paint()
ctx.set_source_rgba(1,1,1,0.035); ctx.set_line_width(1)
for x in range(0,W,60): ctx.move_to(x,0); ctx.line_to(x,H)
for y in range(0,H,60): ctx.move_to(0,y); ctx.line_to(W,y)
ctx.stroke()
ctx.save(); ctx.translate(540,1035); z=0.9; ctx.scale(z,z)
ctx.save(); ctx.translate(14,22); S.draw_plane_shape(ctx,fill=(0,0,0,0.25)); ctx.restore()
S.draw_plane_shape(ctx,stroke=(0.95,0.97,1,0.97),lw=3.6)
for x,y,s in S.RED_DOTS: S.draw_dot(ctx,x,y,9*s,S.RED,1,ring=True)
ctx.restore()
rg=cairo.RadialGradient(W/2,H*0.62,280,W/2,H*0.62,1100); rg.add_color_stop_rgba(0,0,0,0,0); rg.add_color_stop_rgba(1,0,0,0,0.6); ctx.set_source(rg); ctx.paint()
lg=cairo.LinearGradient(0,0,0,700); lg.add_color_stop_rgba(0,0.03,0.05,0.08,0.75); lg.add_color_stop_rgba(0.7,0.03,0.05,0.08,0.55); lg.add_color_stop_rgba(1,0.03,0.05,0.08,0); ctx.set_source(lg); ctx.rectangle(0,0,W,700); ctx.fill()
arr=np.ndarray((H,W,4),np.uint8,surf.get_data()).copy()
img=Image.fromarray(arr[:,:,[2,1,0,3]],"RGBA"); d=ImageDraw.Draw(img)
# red tag top-left
f=S.font(S.FONT_BLACK,52); txt="军方差点加错了地方"; tw=f.getlength(txt)
d.rounded_rectangle((48,52,48+tw+56,52+92),radius=12,fill=(226,38,32,255))
d.text((48+28,52+46),txt,font=f,fill=(255,255,255,255),anchor="lm")
S.text_line(d,S.parse("满身弹孔的地方"),540,300,124,stroke=10)
S.text_line(d,S.parse("反而"),540,440,124,stroke=10)
S.text_line(d,S.parse("[不用加固]"),540,612,160,stroke=12)
# series mark bottom-right
f2=S.font(S.FONT_BOLD,40); f3=S.font(S.FONT_BLACK,64)
d.text((1032,1392),"02",font=f3,fill=(255,212,0,255),anchor="rs",stroke_width=4,stroke_fill=(0,0,0,255))
d.text((1032-f3.getlength("02")-14,1384),"三十秒一问",font=f2,fill=(255,255,255,235),anchor="rs",stroke_width=3,stroke_fill=(0,0,0,255))
d.text((48,1388),"示意图",font=S.font(S.FONT_MED,30),fill=(225,232,240,160),anchor="ls")
img.convert("RGB").save(sys.argv[1])
img.convert("RGB").resize((120,160),Image.LANCZOS).save(sys.argv[1].replace('.png','_120.png'))
