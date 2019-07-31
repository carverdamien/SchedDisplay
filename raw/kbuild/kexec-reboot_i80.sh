#!/bin/bash

set -e -x -u

KERNEL=$(uname -r)
VMLINUX="/boot/vmlinuz-${KERNEL}"
INITRD="/boot/initrd.img-${KERNEL}"
CMDLINE='root=UUID=754fa6b1-bb34-449a-9b95-41897013bded ro quiet'

sudo kexec \
     -l "${VMLINUX}" \
     --append="${CMDLINE}" \
     --initrd="${INITRD}"
sudo kexec -e
