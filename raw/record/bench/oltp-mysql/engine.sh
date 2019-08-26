#!/bin/bash

set -e -u
source host/${HOSTNAME}/${BENCH}/config

help() {
    echo "Usage: $0 [status|start|stop|help|prepare|cleanup|client]"
    exit 1
}

main() {
    [[ $# -ge 1 ]] ||
	help
    cmd=$1
    shift
    check_engine_version
    case "$cmd" in
	status)
	    status "$@"
	    ;;
	start)
	    start "$@"
	    ;;
	stop)
	    stop "$@"
	    ;;
	help)
	    help "$@"
	    ;;
	prepare)
	    prepare "$@"
	    ;;
	cleanup)
	    cleanup "$@"
	    ;;
	client)
	    egine_client "$@"
	    ;;
	*)
	    fatal "Unknown cmd: ${cmd}"
	;;
    esac
}

egine_client() { "${ENGINE_CLIENT_BIN}" ${ENGINE_CLIENT_DEFAULT_ARGS} "$@"; }

status() {
    if is_running
    then
	info "Running"
    else
	info "Stopped"
    fi
    if is_prepared
    then
	info "Prepared"
    else
	info "Cleaned"
    fi
}

is_running() { pgrep_engine_daemon > /dev/null; }
is_stopped() { ! is_running; }
is_prepared() { [[ -n "$(find ${ENGINE_DATA_DIR} -maxdepth 1 -mindepth 1 2>/dev/null)" ]]; }
is_cleaned() { ! is_prepared; }

start() {
    is_prepared ||
	fatal "${ENGINE_DAEMON_NAME} is not prepared"
    is_stopped ||
	ok "${ENGINE_DAEMON_NAME} already running"
    "${ENGINE_DAEMON_BIN}" ${ENGINE_DAEMON_DEFAULT_ARGS} "$@" &
}

pgrep_engine_daemon() {
    pgrep "${ENGINE_DAEMON_NAME}" | grep "^$(cat "${ENGINE_DAEMON_PID_FILE}" 2>/dev/null)\$" 2>/dev/null
}

stop() {
    is_running ||
	ok "${ENGINE_DAEMON_NAME} already stopped"
    kill $(pgrep_engine_daemon)
}

prepare() {
    is_stopped ||
	fatal "${ENGINE_DAEMON_NAME} is running"
    is_cleaned ||
	ok "${ENGINE_DAEMON_NAME} is already prepared"
    check_engine_dir
    cd ${ENGINE_DATA_DIR}
    "${ENGINE_INIT_BIN}" ${ENGINE_INIT_DEFAULT_ARGS} "$@"
}

cleanup() {
    is_stopped ||
	fatal "${ENGINE_DAEMON_NAME} is running"
    is_prepared ||
	ok "${ENGINE_DAEMON_NAME} is already cleaned up"
    find "${ENGINE_BASE_DIR}" -maxdepth 1 -mindepth 1 -exec rm -fr {} \;
}

check_engine_version() { "${ENGINE_DAEMON_BIN}" --version | grep -q "${ENGINE_VERSION}"; }
check_engine_dir() {
    for dir in ${MKDIR_CHOWN_IF_DIRS_DO_NOT_EXIST}
    do
	if ! ([[ -d "${!dir}" ]] && [[ "$(stat --format %U ${!dir})" == "${ENGINE_DAEMON_USER}" ]])
	then
	    mkdir -p "${!dir}"
	    chown ${ENGINE_DAEMON_USER}:${ENGINE_DAEMON_GROUP} "${!dir}"
	fi
    done
    for file in ${TOUCH_CHOWN_IF_FILES_DO_NOT_EXIST}
    do
	if ! ([[ -f "${!file}" ]] && [[ "$(stat --format %U ${!file})" == "${ENGINE_DAEMON_USER}" ]])
	then
	    touch "${!file}"
	    chown ${ENGINE_DAEMON_USER}:${ENGINE_DAEMON_GROUP} "${!file}"
	fi
    done
}

main "$@"