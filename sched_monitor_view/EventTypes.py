EVENT = [
    'EXEC_EVT',
    'EXIT_EVT',
    'WAKEUP',
    'WAKEUP_NEW',
    'BLOCK',
    'BLOCK_IO',
    'BLOCK_LOCK',
    'WAKEUP_LOCK',
    'WAKER_LOCK',
    'FORK_EVT',
    'TICK_EVT',
    'CTX_SWITCH',
    'MIGRATE_EVT',
    'RQ_SIZE',
    'IDLE_BALANCE_BEG',
    'IDLE_BALANCE_END',
    'PERIODIC_BALANCE_BEG',
    'PERIODIC_BALANCE_END',
]
ID = {
    EVENT[i] : i
    for i in range(len(EVENT))
}
