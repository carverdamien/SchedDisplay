#!/bin/bash

set -x -e
export BENCH=bench/oltp-mysql
export PATH_TO_IPANEMA_MODULE=''
export TIMEOUT=36000
export MONITORING TASKS OUTPUT

for MONITORING in monitoring/all monitoring/nop
do
	for TASKS 80 160 320
	do
		OUTPUT="output/BENCH=$(basename ${BENCH})/MONITORING=$(basename ${MONITORING})/${TASKS}-$(uname -r)"
		./entrypoint
	done
done
