#!/bin/bash

set -x -e -u

kexec_reboot() {
if [[ "${KERNEL}" != "$(uname -r)" ]]
then
VMLINUZ="/boot/vmlinuz-${KERNEL}"
INITRD="/boot/initrd.img-${KERNEL}"
[ -f "${VMLINUZ}" ]
[ -f "${INITRD}" ]
echo "${KERNEL}" > kexec_reboot.attempt
sync
kexec -l "${VMLINUZ}" --append="$( cat /proc/cmdline )" --initrd="${INITRD}"
kexec -e
else
if [[ "$(cat kexec_reboot.attempt)" == "${KERNEL}" ]]
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

for KERNEL in 4.19.0-ipanema-4.19.0-ipanema-g131fda29324a 4.19.0-ipanema-g9ee5320702ba 4.19.0-ipanema-g8acfcf3f3364
do
for MONITORING in monitoring/all monitoring/cpu-energy-meter monitoring/nop
do
        for TASKS in 80 160 320
        do
                echo ${NO_TURBO} | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
                echo ${SCALING_GOVERNOR} | sudo tee /sys/devices/system/cpu/cpufreq/policy*/scaling_governor
                OUTPUT="output/BENCH=$(basename ${BENCH})/MONITORING=$(basename ${MONITORING})/${TASKS}-$(uname -r)"
                TAR="${OUTPUT}.tar"
                if ! [[ -e "${TAR}" ]]
                then
		    kexec_reboot
		    ./entrypoint
                fi
        done
done
done
