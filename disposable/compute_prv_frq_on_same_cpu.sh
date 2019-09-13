#!/bin/bash
set -x
find examples/trace -name '*.tar' -exec ./docker_entrypoint_no_tty ./disposable/compute_prv_frq_on_same_cpu.py {} \;
