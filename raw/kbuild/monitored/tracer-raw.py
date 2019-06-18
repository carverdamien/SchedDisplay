#!/usr/bin/env python3
import sys, mmap, struct
from enum import Enum
import pandas as pd

class Event(Enum):
    EXEC_EVT    = 0                     # timestamp EXEC pid
    EXIT_EVT    = 1                     # timestamp EXIT pid
    WAKEUP      = 2                     # timestamp WAKEUP pid
    WAKEUP_NEW  = 3                     # timestamp WAKEUP_NEW pid
    BLOCK       = 4                     # timestamp BLOCK pid
    BLOCK_IO    = 5                     # timestamp BLOCK_IO pid
    BLOCK_LOCK  = 6                     # timestamp BLOCK_LOCK pid addr
    WAKEUP_LOCK = 7                     # timestamp WAKEUP_LOCK pid addr
    WAKER_LOCK  = 8                     # timestamp WAKER_LOCK pid addr
    FORK_EVT    = 9                     # timestamp FORK pid ppid
    TICK_EVT    = 10                    # timestamp TICK pid need_resched
    CTX_SWITCH  = 11                    # timestamp CTX_SWITCH pid next
    MIGRATE_EVT = 12                    # timestamp MIGRATE pid old_cpu new_cpu
    RQ_SIZE     = 13                    # timestamp RQ_SIZE current size count
    IDLE_BALANCE_BEG = 14               # timestamp IDL_BLN_BEG pid sched_domain_addr
    IDLE_BALANCE_END = 15               # timestamp IDL_BLN_END pid sched_group_addr
    PERIODIC_BALANCE_BEG = 16           # timestamp PER_BLN_BEG pid sched_domain_addr
    PERIODIC_BALANCE_END = 17           # timestamp PER_BLN_END pid sched_group_addr
    SCHED_MONITOR_TRACER_NR_EVENTS = 18 # keep last
SchedTracerEntrySize = 8+4+4+8
SchedTracerEntries = {
    'addr' : [
        Event.BLOCK_LOCK,
        Event.WAKEUP_LOCK,
        Event.WAKER_LOCK,
        Event.FORK_EVT,
        Event.TICK_EVT,
        Event.CTX_SWITCH,
        Event.IDLE_BALANCE_BEG,
        Event.IDLE_BALANCE_END,
        Event.PERIODIC_BALANCE_BEG,
        Event.PERIODIC_BALANCE_END,
    ],
    'arg0,arg1' : [
        Event.MIGRATE_EVT,
        Event.RQ_SIZE,
    ],
    'None' : [
        Event.EXEC_EVT,
        Event.EXIT_EVT,
        Event.WAKEUP,
        Event.WAKEUP_NEW,
        Event.BLOCK,
        Event.BLOCK_IO,
    ],
}
    
i_opath = sys.argv[1]

with open(i_opath, 'r+b') as f:
    mm = mmap.mmap(f.fileno(), 0)
    assert(len(mm)%SchedTracerEntrySize == 0)
    data = []
    for i in range(len(mm)//SchedTracerEntrySize):
        entry = mm[i*SchedTracerEntrySize:i*SchedTracerEntrySize+SchedTracerEntrySize]
        head = entry[:16]
        tail = entry[16:]
        timestamp, pid, event = struct.unpack('<Qii',head)
        addr, = struct.unpack('<Q',tail)
        arg0, arg1 = struct.unpack('<ii',tail)
        data.append({
            'timestamp' : timestamp,
            'pid' : pid,
            'event' : event,
            'addr' : addr,
            'arg0' : arg0,
            'arg1' : arg1,
        })
    df = pd.DataFrame(data).set_index('timestamp')
    print(df[ (df['event'] == 13) | (df['event'] == 4) | (df['event'] == 2) ])
