#!/bin/bash

TASKS=256
TIMEOUT=36000

for NO_TURBO in '0' '1'
do
    for SCALING_GOVERNOR in 'performance' 'powersave'
    do
	for PATH_TO_IPANEMA_MODULE in '' "/lib/modules/$(uname -r)/source/ipanema/modules/cfs_wwc_local_new_unblock.ko"
	do
	    for MONITOR in '' 'y'
	    do
		echo ${NO_TURBO} | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
		echo ${SCALING_GOVERNOR} | sudo tee /sys/devices/system/cpu/cpufreq/policy*/scaling_governor
		sudo MONITOR=${MONITOR} TIMEOUT=${TIMEOUT} PATH_TO_IPANEMA_MODULE=${PATH_TO_IPANEMA_MODULE} TASKS=${TASKS} ./entrypoint
	    done
	done
    done
done
