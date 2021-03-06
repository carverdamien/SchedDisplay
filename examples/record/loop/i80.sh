#!/bin/bash

set -x -e -u

function kexec_reboot {
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

function run_bench {
    echo ${NO_TURBO} | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
    echo ${SCALING_GOVERNOR} | sudo tee /sys/devices/system/cpu/cpufreq/policy*/scaling_governor
    TAR="${OUTPUT}.tar"
    if ! [[ -e "${TAR}" ]]
    then
	kexec_reboot
	./entrypoint
    fi
}

export BENCH=bench/oltp-mysql
export PATH_TO_IPANEMA_MODULE=''
export TIMEOUT=36000
export MONITORING_SCHEDULED=y
export MONITORING_START_DELAY=60
export MONITORING_STOP_DELAY=10
export MONITORING TASKS OUTPUT KERNEL
export IPANEMA_MODULE=
NO_TURBO=0
SCALING_GOVERNOR='powersave' # or performance

DEFAULT_KERNEL=4.19.0-linux-4.19-ipanema-g0e4249a3eec1
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
	    OUTPUT="output/BENCH=$(basename ${BENCH})/MONITORING=$(basename ${MONITORING})/${TASKS}-${KERNEL}"
	    run_bench
	done
    done
done

# exit 0

# IPANEMA
for KERNEL in ${DEFAULT_KERNEL}
do
    PATH_TO_IPANEMA_MODULES="/lib/modules/$(uname -r)/kernel/kernel/sched/ipanema"
    for IPANEMA_MODULE in cfs_wwc ule_wwc
    do
	for MONITORING in ${MONITORINGS}
	do
	    for TASKS in 80 160 320
	    do
		OUTPUT="output/BENCH=$(basename ${BENCH})/MONITORING=$(basename ${MONITORING})/IPANEMA=$(basename ${IPANEMA_MODULE})/${TASKS}-${KERNEL}"
		run_bench
	    done
	done
    done
done


#################################################
# Running kbuild sched
#################################################
BENCH=bench/kbuild
export TARGET=kernel/sched/
MONITORING_SCHEDULED=n
IPANEMA_MODULE=
for KERNEL in ${KERNELS}
do
    for MONITORING in ${MONITORINGS}
    do
	for TASKS in 32
	do
	    OUTPUT="output/BENCH=$(basename ${BENCH})-$(basename ${TARGET})/MONITORING=$(basename ${MONITORING})/${TASKS}-${KERNEL}"
	    run_bench
	done
    done
done


#################################################
# Running NAS
#################################################
BENCH_NAMES=(	bt cg dc ep ft is lu mg sp sp ua ua )
BENCH_CLASSES=( B  C  A  C  C  D  B  D  A  B  B  C )
MONITORING_SCHEDULED=n
IPANEMA_MODULE=
export BENCH_NAME=
export BENCH_CLASS=

for I in ${!BENCH_NAMES[@]}
do
    for KERNEL in ${KERNELS}
    do
        for MONITORING in ${MONITORINGS}
        do
            for TASKS in 80 160
            do
                BENCH_NAME=${BENCH_NAMES[$I]}
                BENCH_CLASS=${BENCH_CLASSES[$I]}
                BENCH=bench/nas
                OUTPUT="output/BENCH=$(basename ${BENCH})_${BENCH_NAME}.${BENCH_CLASS}/MONITORING=$(basename ${MONITORING})/${TASKS}-${KERNEL}"
                run_bench
            done
        done
    done
done

# IPANEMA
KERNEL=${DEFAULT_KERNEL}
PATH_TO_IPANEMA_MODULES="/lib/modules/$(uname -r)/kernel/kernel/sched/ipanema"

for I in ${!BENCH_NAMES[@]}
do
    for IPANEMA_MODULE in cfs_wwc ule_wwc
    do
        for MONITORING in ${MONITORINGS}
        do
            for TASKS in 80 160
            do
                BENCH_NAME=${BENCH_NAMES[$I]}
                BENCH_CLASS=${BENCH_CLASSES[$I]}
                BENCH=bench/nas
                OUTPUT="output/BENCH=$(basename ${BENCH})_${BENCH_NAME}.${BENCH_CLASS}/MONITORING=$(basename ${MONITORING})/IPANEMA=$(basename ${IPANEMA_MODULE})/${TASKS}-${KERNEL}"
                run_bench
            done
        done
    done
done

