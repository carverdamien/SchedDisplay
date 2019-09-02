#!/bin/bash

set -x -e -u

kexec_reboot() {
    if [[ ${KERNEL} != $(uname -r) ]]
    then
	VMLINUZ="/boot/vmlinuz-${KERNEL}"
	INITRD="/boot/initrd.img-${KERNEL}"
	[ -f "${VMLINUZ}" ]
	[ -f "${INITRD}" ]
	echo "${KERNEL}" > kexec_reboot.attempt
	kexec -l "${VMLINUZ}" --append="$( cat /proc/cmdline )" --initrd="${INITRD}"
	rm -f "./loop/${KERNEL}.lock"
	sync
	# sleep inf # debug
	kexec -e
    else
	if [[ -f kexec_reboot.attempt ]] && [[ $(cat kexec_reboot.attempt) != ${KERNEL} ]]
	then
	    echo 'Help me'
	    sleep inf
	fi
    fi
}

export BENCH=bench/oltp-mysql
export PATH_TO_IPANEMA_MODULE=''
export TIMEOUT=36000
export MONITORING_SCHEDULED=y
export MONITORING_START_DELAY=60
export MONITORING_STOP_DELAY=10
export MONITORING TASKS OUTPUT KERNEL
NO_TURBO=0
SCALING_GOVERNOR='powersave' # or performance

DEFAULT_KERNEL=4.19.0-linux-4.19-ipanema-gd6437e6b2bdd
KERNELS="${DEFAULT_KERNEL} 4.19.0-patch-local-g131fda29324a 4.19.0-patch-local-light-g9ee5320702ba 4.19.0-patch-sched-freq-g710892956166"
MONITORINGS="monitoring/all monitoring/cpu-energy-meter monitoring/nop"

#################################################
# Running mysql OLTP
#################################################
for KERNEL in ${KERNELS}
do
    for MONITORING in ${MONITORINGS}
    do
	for TASKS in 80 160 320
	do
	    echo ${NO_TURBO} | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
	    echo ${SCALING_GOVERNOR} | sudo tee /sys/devices/system/cpu/cpufreq/policy*/scaling_governor
	    OUTPUT="output/BENCH=$(basename ${BENCH})/MONITORING=$(basename ${MONITORING})/${TASKS}-${KERNEL}"
	    TAR="${OUTPUT}.tar"
	    if ! [[ -e "${TAR}" ]]
	    then
		kexec_reboot
		./entrypoint
	    fi
	done
    done
done

# exit 0

# IPANEMA
build_ipanema_module() {
    (cd $(dirname ${PATH_TO_IPANEMA_MODULE}); make -B KERNEL=../..)
}
for KERNEL in ${DEFAULT_KERNEL}
do
    for PATH_TO_IPANEMA_MODULE in "/lib/modules/$(uname -r)/source/ipanema/modules/cfs_wwc.ko" \
				      "/lib/modules/$(uname -r)/source/ipanema/modules/ule_wwc.ko"
    do
	for MONITORING in ${MONITORINGS}
	do
	    for TASKS in 80 160 320
	    do
		echo ${NO_TURBO} | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
		echo ${SCALING_GOVERNOR} | sudo tee /sys/devices/system/cpu/cpufreq/policy*/scaling_governor
		OUTPUT="output/BENCH=$(basename ${BENCH})/MONITORING=$(basename ${MONITORING})/IPANEMA=$(basename ${PATH_TO_IPANEMA_MODULE} .ko)/${TASKS}-${KERNEL}"
		TAR="${OUTPUT}.tar"
		if ! [[ -e "${TAR}" ]]
		then
		    kexec_reboot
		    build_ipanema_module
		    ./entrypoint
		fi
	    done
	done
    done
done


#################################################
# Running kbuild sched
#################################################
BENCH=bench/kbuild
export TARGET=sched
MONITORING_START_DELAY=0
MONITORING_STOP_DELAY=100000
for KERNEL in ${KERNELS}
do
    for MONITORING in ${MONITORINGS}
    do
	for TASKS in 32
	do
	    echo ${NO_TURBO} | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
	    echo ${SCALING_GOVERNOR} | sudo tee /sys/devices/system/cpu/cpufreq/policy*/scaling_governor
	    OUTPUT="output/BENCH=$(basename ${BENCH})/MONITORING=$(basename ${MONITORING})/${TASKS}-${KERNEL}"
	    TAR="${OUTPUT}.tar"
	    if ! [[ -e "${TAR}" ]]
	    then
		kexec_reboot
		./entrypoint
	    fi
	done
    done
done
