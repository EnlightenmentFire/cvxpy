import sys, skia
sys.path.insert(0,'.')
import illus
from geo import W,H
s=skia.Surface(W,H); c=s.getCanvas()
illus.draw(c, 3.0, door=1.0, light=1.0, mapu=1.0, mglow=1.0, lit=(1,1))
s.makeImageSnapshot().save('/home/user/work/vid/illus_test.png')
