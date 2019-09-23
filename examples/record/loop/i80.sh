#!/bin/bash

set -x -e -u

[ $HOSTNAME = i80 ]

function kexec_reboot {
    BOOT_IMAGE="/boot/vmlinuz-${KERNEL}"
    INITRD="/boot/initrd.img-${KERNEL}"
    [ -f "${BOOT_IMAGE}" ]
    [ -f "${INITRD}" ]
    case ${SLEEP_STATE} in
	'y')
	    APPEND='root=UUID=754fa6b1-bb34-449a-9b95-41897013bded ro quiet'
	    ;;
	'n')
	    APPEND='root=UUID=754fa6b1-bb34-449a-9b95-41897013bded ro quiet processor.max_cstate=1 intel_idle.max_cstate=0'
	    ;;
	*)
	    echo 'SLEEP_STATE must be [y,n]'
	    exit 1
	    ;;
    esac
    CMDLINE="BOOT_IMAGE=${BOOT_IMAGE} ${APPEND}"
    CURRENT_CMDLINE="$(cat /proc/cmdline)"
    if [ "${CMDLINE}" != "${CURRENT_CMDLINE}" ]
    then
	echo "${CMDLINE}" > kexec_reboot.attempt
	# kexec -l "${BOOT_IMAGE}" --append="${APPEND}" --initrd="${INITRD}"
	kexec -l "${BOOT_IMAGE}" --command-line="${CMDLINE}" --initrd="${INITRD}"
	rm -f "./loop/${KERNEL}.lock"
	sync
	# sleep inf # debug
	kexec -e
    else
	if [ -f kexec_reboot.attempt ] && [ "$(cat kexec_reboot.attempt)" != "${CMDLINE}" ]
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
SLEEP_STATE=y
NO_TURBO=0
SCALING_GOVERNORS='powersave performance'
SCALING_GOVERNOR='powersave'

DEFAULT_KERNEL="4.19.0-linux-4.19-ipanema-g2bd98bf652cb"
# Before setting DEFAULT_KERNEL=4.19.0-linux-4.19-ipanema-g0e4249a3eec1,
# we need to understand why there were soft lockups with cfs_wwc.
#
# Soft lockups happened again with 4.19.0-linux-4.19-ipanema-g0e4249a3eec1,
# Removing it because I assume it was not running cfs_wwc.
KERNELS="${DEFAULT_KERNEL} 4.19.0-patch-local-g131fda29324a 4.19.0-patch-local-light-g9ee5320702ba 4.19.0-patch-sched-freq-g710892956166"
MONITORINGS="monitoring/all monitoring/cpu-energy-meter monitoring/nop"

#################################################
# Running mysql OLTP
#################################################
SLP=(y         n          )
GOV=(powersave performance)
RPT=(1         5          )
for I in ${!SLP[@]}
do
    SLEEP_STATE=${SLP[$I]}
    SCALING_GOVERNOR=${GOV[$I]}
    REPEAT=${RPT[$I]}
    # Reboot between repeats
    for N in $(seq ${REPEAT})
    do
	for KERNEL in ${KERNELS}
	do
	    for MONITORING in ${MONITORINGS}
	    do
		for TASKS in 32 64 80 160 320
		do
		    OUTPUT="output/"
		    OUTPUT+="BENCH=$(basename ${BENCH})/"
		    OUTPUT+="POWER=${SCALING_GOVERNOR}-${SLEEP_STATE}/"
		    OUTPUT+="MONITORING=$(basename ${MONITORING})/"
		    OUTPUT+="${TASKS}-${KERNEL}/${N}"
		    run_bench
		done
	    done
	done
    done
done

# IPANEMA
for I in ${!SLP[@]}
do
    SLEEP_STATE=${SLP[$I]}
    SCALING_GOVERNOR=${GOV[$I]}
    REPEAT=${RPT[$I]}
    # Reboot between repeats
    for N in $(seq ${REPEAT})
    do
	for KERNEL in ${DEFAULT_KERNEL}
	do
	    for IPANEMA_MODULE in cfs_wwc ule_wwc
	    do
		for MONITORING in ${MONITORINGS}
		do
		    for TASKS in 32 64 80 160 320
		    do
			OUTPUT="output/"
			OUTPUT+="BENCH=$(basename ${BENCH})/"
			OUTPUT+="POWER=${SCALING_GOVERNOR}-${SLEEP_STATE}/"
			OUTPUT+="MONITORING=$(basename ${MONITORING})/"
			OUTPUT+="IPANEMA=$(basename ${IPANEMA_MODULE})/"
			OUTPUT+="${TASKS}-${KERNEL}/${N}"
			run_bench
		    done
		done
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
SLEEP_STATE=y
SCALING_GOVERNOR=powersave
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
# Running llvm cmake
#################################################

BENCH=bench/llvmcmake
MONITORING_SCHEDULED=n
IPANEMA_MODULE=
for KERNEL in ${KERNELS}
do
    for MONITORING in ${MONITORINGS}
    do
	OUTPUT="output/BENCH=$(basename ${BENCH})/MONITORING=$(basename ${MONITORING})/${KERNEL}"
	run_bench
    done
done

#################################################
# Running NAS
#################################################
BENCH_NAMES=(	bt cg dc ep ft    lu mg sp sp ua ua ) # is
BENCH_CLASSES=( B  C  A  C  C     B  D  A  B  B  C )  # D
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

for I in ${!BENCH_NAMES[@]}
do
    for IPANEMA_MODULE in cfs_wwc ule_wwc
    do
        for MONITORING in ${MONITORINGS}
        do
            for TASKS in 80 160
            do
                break
                BENCH_NAME=${BENCH_NAMES[$I]}
                BENCH_CLASS=${BENCH_CLASSES[$I]}
                BENCH=bench/nas
                OUTPUT="output/BENCH=$(basename ${BENCH})_${BENCH_NAME}.${BENCH_CLASS}/MONITORING=$(basename ${MONITORING})/IPANEMA=$(basename ${IPANEMA_MODULE})/${TASKS}-${KERNEL}"
                run_bench
            done
        done
    done
done

