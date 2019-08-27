#!/bin/bash

set -x -e
export BENCH=bench/oltp-mysql
export PATH_TO_IPANEMA_MODULE=''
export TIMEOUT=36000
export MONITORING_SCHEDULED=y
export MONITORING_START_DELAY=60
export MONITORING_STOP_DELAY=10
export MONITORING TASKS OUTPUT
NO_TURBO=0
SCALING_GOVERNOR='powersave' # or performance

for MONITORING in monitoring/all monitoring/nop
do
	for TASKS in 80 160 320
	do
		echo ${NO_TURBO} | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
		echo ${SCALING_GOVERNOR} | sudo tee /sys/devices/system/cpu/cpufreq/policy*/scaling_governor
		OUTPUT="output/BENCH=$(basename ${BENCH})/MONITORING=$(basename ${MONITORING})/${TASKS}-$(uname -r)"
		./entrypoint
	done
done
