#!/bin/bash

set -e -x -u

KERNEL=$(uname -r)
VMLINUX="/boot/vmlinuz-${KERNEL}"
INITRD="/boot/initrd.img-${KERNEL}"
CMDLINE='root=UUID=754fa6b1-bb34-449a-9b95-41897013bded ro quiet processor.max_cstate=1 intel_idle.max_cstate=0'

sudo kexec \
     -l "${VMLINUX}" \
     --append="${CMDLINE}" \
     --initrd="${INITRD}"
sudo kexec -e
