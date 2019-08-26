#!/bin/bash

set -e -u
source host/${HOSTNAME}/${BENCH}/config

function usage {
    echo "Usage: $0 CLIENTS [all|prepare|run|cleanup]"
    exit 1
}

main() {

    case $# in
	1|2);;
	*)
	    usage
	    ;;
    esac
    
    re='^[0-9]+$'
    [[ $1 =~ $re ]] ||
	fatal "$1 is not an integer"
    
    CLIENTS=$1

    check_simulator_version
    
    until engine_daemon_is_ready
    do
	info "Waiting for ${ENGINE_DAEMON_NAME} to be ready"
	sleep 1
    done
    
    simulator ${2:-"all"}
    echo "============================================"
}

prepare_db() {
    cleanup_db || true
    create_db
}

check_simulator_version() { "${CLIENT_BIN}" --version | grep -q "${CLIENT_VERSION}"; }

simulator() {
    cmd="$1"
    
    case "${cmd}" in
	all)
	    simulator cleanup || true
	    simulator prepare
	    simulator run
	    return 0
	;;
	prepare)
	    if ! check_db_exists || ! check_db_size
	    then
		prepare_db
		client ${cmd}
	    fi
	    check_db_size ||
	    fatal "check_db_size failed"
	;;
	run)
	    client ${cmd}
	    get_engine_daemon_config
	;;
	cleanup)
	    client ${cmd}
	    cleanup_db
	;;
	*)
	    fatal "Unkown cmd: ${cmd}"
	;;
    esac
}

main "$@"