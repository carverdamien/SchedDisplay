#!/bin/bash
set -e -x -u
TAR="$1"
SRC_DIR=/mnt/data/damien/git/carverdamien/SchedDisplay/examples/record/output/
DSTS="damien@amd48b-systeme.rsr.lip6.fr:/mnt/data/damien/git/carverdamien/SchedDisplay/examples/trace/ damien@i44.rsr.lip6.fr:/mnt/data/damien/git/carverdamien/SchedDisplay/examples/trace/"
for DST in ${DSTS}
do
    rsync -e "ssh -i /home/damien/.ssh/id_rsa" --size-only -rvP "${SRC_DIR}" "${DST}"
done
if [ -x ./host/${HOSTNAME}/notify ]
then
    ./host/${HOSTNAME}/notify "New Record: ${TAR}"
fi
