#!/bin/bash
set -x
for TASKS in 40 1000 2000 4000 6000 8000 10000
do
    TIMEOUT=60 PATH_TO_IPANEMA_MODULE= TASKS=${TASKS} ./entrypoint
    mv ouput.hdf5 ${TASKS}-linux.hdf5
done
