#!/bin/bash
set -e
exec >> $0
echo ${HOSTNAME}:$(date)
perf stat -e cycles,instructions,cache-misses -- python3 ./disposable/bench.py 2>&1
exit 0
