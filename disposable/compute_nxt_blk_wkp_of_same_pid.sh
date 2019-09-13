#!/bin/bash
set -x
find examples/trace -name '*.tar' -exec ./docker_entrypoint_no_tty ./disposable/compute_nxt_blk_wkp_of_same_pid.py {} \;
