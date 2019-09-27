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
	if [[ -x ./host/${HOSTNAME}/callback_run_bench.sh ]]
	then
	    ./host/${HOSTNAME}/callback_run_bench.sh "${TAR}" || true
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
IPANEMA_MODULES="cfs_wwc ule_wwc" # cfs_wwc_ipa cfs_wwc_ipa

#################################################
# Running mysql OLTP
#################################################
SLP=(y         n          )
GOV=(powersave performance)
RPT=(1         1          )
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
	    for IPANEMA_MODULE in ${IPANEMA_MODULES}
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
    for IPANEMA_MODULE in ${IPANEMA_MODULES}
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

#################################################
# Running Phoronix
#################################################
IPANEMA_MODULE=
BENCH=bench/phoronix
export PHORONIX
PHORONIXES="compress-7zip compress-gzip compress-pbzip2 compress-rar compress-xz compress-zstd"
# PHORONIXES+="blender fio dbench iozone brl-cad core-latency etqw-demo-irq aircrack-ng pts-self-test"
# PHORONIXES+="pgbench" # might be interesting but too long
PHORONIXES+="apache blogbench caffe clpeak cryptsetup darktable ethminer gimp gnupg octave-benchmark openssl redis selenium selenium-top-sites sqlite tesseract-ocr"
PHORONIXES+="aio-stress aobench aom-av1 apache apache-siege appleseed arrayfire asmfish battery-power-usage blake2 blogbench bork botan build-apache build-eigen build-firefox build-gcc build-imagemagick build-linux-kernel build-llvm build-mplayer build-php build-webkitfltk bullet byte cachebench caffe clomp cloverleaf clpeak comd-cl compilebench compress-7zip compress-gzip compress-lzma compress-pbzip2 compress-rar compress-xz compress-zstd coremark cp2k cpp-perf-bench cpuminer-opt crafty c-ray cryptsetup ctx-clock cyclictest cython-bench dacapobench darktable dav1d dcraw dolfyn ebizzy encode-flac encode-mp3 encode-wavpack espeak ethminer ethr fahbench ffmpeg ffte fftw fhourstones fs-mark geekbench gimp git glibc-bench gmpbench gnupg go-benchmark gpu-residency gromacs hackbench hdparm-read himeno hint hmmer hpcc hpcg idle idle-power-usage indigobench interbench iperf java-gradle-perf java-jmh java-scimark2 john-the-ripper juliagpu lammps lczero llvm-test-suite luajit lulesh-cl luxmark lzbench mafft mandelbulbgpu mandelgpu mbw mcperf memtier-benchmark mencoder minion mkl-dnn mpcbench m-queens mrbayes multichase mysqlslap namd namd-cuda neatbench nero2d netperf network-loopback nginx node-express-loadtest node-octane noise-level novabench npb n-queens numenta-nab numpy nuttcp octave-benchmark opencv-bench opendwarfs open-porous-media openssl opm-git optcarrot osbench parboil pennant perl-benchmark php phpbench pjdfstest polybench-c postmark povray powertop-wakeups primesieve psstop pybench pymongo-inserts pyopencl qmcpack qmlbench radiance ramspeed rbenchmark redis renaissance rodinia rust-mandel rust-prime sample-pass-fail sample-program schbench scikit-learn scimark2 selenium selenium-top-sites serial-loopback smallpt smallpt-gpu smart sockperf spec-cpu2017 spec-jbb2015 sqlite startup-time stockfish stream stressapptest stresscpu2 stress-ng sudokut sunflow svt-av1 svt-hevc svt-vp9 swet sysbench systemd-boot-kernel systemd-boot-total systemd-boot-userspace system-decompress-bzip2 system-decompress-gzip system-decompress-tiff system-decompress-xz system-decompress-zlib system-libjpeg system-libxml2 systester tachyon tensorflow tesseract-ocr tinymembench tiobench tjbench tscp t-test1 ttsiod-renderer tungsten unpack-linux vpxenc v-ray x264 x264-opencl x265 xsbench xsbench-cl y-cruncher"
# Increase total length of bench but will obtain intermediate results earlier
for PHORONIX in ${PHORONIXES}
do
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
	    for MONITORING in monitoring/cpu-energy-meter
	    do
		# for PHORONIX in ${PHORONIXES}
		# do
		    OUTPUT="output/"
		    OUTPUT+="BENCH=$(basename ${BENCH})/"
		    OUTPUT+="POWER=${SCALING_GOVERNOR}-${SLEEP_STATE}/"
		    OUTPUT+="MONITORING=$(basename ${MONITORING})/"
		    OUTPUT+="PHORONIX=${PHORONIX}/"
		    OUTPUT+="${KERNEL}/${N}"
		    run_bench
		# done
	    done
	done
    done
done
done
