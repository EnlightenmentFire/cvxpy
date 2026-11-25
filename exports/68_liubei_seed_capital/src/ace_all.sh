#!/bin/bash
cd /home/user/work/acestep/code && . /home/user/work/acev/bin/activate
for job in base=150 base2=150 push=120 war=120 coda=80; do
  l=${job%%=*}; rm -rf /home/user/work/music/$l
  ACESTEP_VAE_DECODE_CHUNK_SIZE=128 python /home/user/work/proj/ace_music.py /home/user/work/music/tmp_$l $job > /home/user/work/music/ace_$l.log 2>&1
  mv /home/user/work/music/tmp_$l/$l /home/user/work/music/$l
done
echo ALLDONE
