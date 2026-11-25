#!/bin/bash
# Keep the session's cgroup away from its 14.3 GB limit (an OOM there has restarted the machine twice).
# If resident memory of our processes exceeds LIMIT_GB, kill the largest python process and log it.
LIMIT_GB=${LIMIT_GB:-11.5}
LOG=/home/user/wude_build/watchdog.log
M=$(grep memory /proc/self/cgroup | cut -d: -f3)
STAT=/sys/fs/cgroup/memory$M/memory.stat
echo "[$(date +%T)] watchdog on, limit ${LIMIT_GB} GB, stat=$STAT" >> $LOG
while true; do
  rss=$(awk '/^total_rss /{print $2}' $STAT 2>/dev/null)
  [ -z "$rss" ] && rss=$(ps -eo rss= | awk '{s+=$1*1024} END{print s}')
  gb=$(awk -v r="$rss" 'BEGIN{printf "%.2f", r/1073741824}')
  if awk -v g="$gb" -v l="$LIMIT_GB" 'BEGIN{exit !(g>l)}'; then
    victim=$(ps -eo pid=,rss=,args= --sort=-rss | grep -E "python" | grep -v mem_watchdog | head -1)
    pid=$(echo "$victim" | awk '{print $1}')
    echo "[$(date +%T)] RSS ${gb} GB > ${LIMIT_GB}: killing $victim" >> $LOG
    kill -9 "$pid" 2>/dev/null
    sleep 5
  fi
  sleep 2
done
