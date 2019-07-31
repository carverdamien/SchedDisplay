#!/usr/bin/env python3
import sys, h5py, os, mmap, struct, json, itertools
import numpy as np
import pandas as pd
from threading import Thread
from multiprocessing import cpu_count
from tqdm import tqdm

EXEC_EVT = 0

def main():
    o_path, i_path = sys.argv[1:3]
    data = load_data(i_path)
    with h5py.File(o_path, 'w') as f:
        store(f, data)

def load_data(path):
    return {
        'perf_event' : load_json(os.path.join(path, 'perf_event.json')),
        'summary' : load_json(os.path.join(path, 'summary.json')),
        'sched_monitor' : load_sched_monitor(os.path.join(path,'sched_monitor')),
    }

def load_json(path):
    with open(path) as f:
        return json.load(f)

def load_sched_monitor(path):
    path = os.path.join(path, 'tracer-raw')
    if not os.path.exists(path):
        return {}
    df, comm = load_tracer_raw(path)
    return {
        'tracer-raw' : { 'df' : df, 'comm':comm }
    }

def addr_2_comm(addr):
    addr = int(addr)
    b = addr.to_bytes(8, byteorder="little")
    i = 0
    while i < 8 and b[i] > 0:
        i+=1
    return b[:i].decode()

def compute_addr_2_comm(df, sel_exec_evt):
    unique_addr = np.unique(df['addr'][sel_exec_evt])
    # TODO: spawn threads
    return {
        addr : addr_2_comm(addr)
        for addr in unique_addr
    }

def compute_addr_2_comm_id(addr_2_comm):
    keys = list(addr_2_comm.keys())
    # id 0 reserved for comm unknown
    return {
        keys[i] : i+1
        for i in range(len(keys))
    }, {
        addr_2_comm[keys[i]]:i+1
        for i in range(len(keys))
    }

def compute_dfcomm(df):
    # By default comm is unknown
    df_addr = np.array(df['addr'])
    df_pid = np.array(df['pid'])
    df_timestamp = np.array(df['timestamp'])
    df_event = np.array(df['event'])
    df_comm = np.zeros(len(df), dtype=int)
    sel_exec_evt = df_event == EXEC_EVT
    addr_2_comm = compute_addr_2_comm(df, sel_exec_evt)
    print(addr_2_comm)
    addr_2_comm_id, comm = compute_addr_2_comm_id(addr_2_comm)
    print(addr_2_comm_id)
    print(comm)
    unique_pid = np.unique(df_pid)
    unique_pid = np.random.permutation(unique_pid)
    nr_threads = cpu_count()
    # nr_threads = 1 # debug
    def _compute_dfcomm_of(pid):
        sel_pid = df_pid == pid
        my_sel_exec_evt = sel_pid & sel_exec_evt
        it = itertools.zip_longest(
            df_addr[my_sel_exec_evt],
            df_timestamp[my_sel_exec_evt],
        )
        for my_addr, my_timestamp in it:
            my_comm_id = addr_2_comm_id[my_addr]
            sel = sel_pid & (df_timestamp >= my_timestamp)
            df_comm[sel] = my_comm_id
    def compute_dfcomm_of(tid, pids):
        for pid in tqdm(pids, position=tid):
            _compute_dfcomm_of(pid)
    def spawn(tid):
        # Static distribution of pids
        nr_pid_per_thread = len(unique_pid)//nr_threads
        first = nr_pid_per_thread * tid
        last  = min(first + nr_pid_per_thread, len(unique_pid))
        # print(first, last)
        pids = unique_pid[first:last]
        args=(tid, pids,)
        t = Thread(target=compute_dfcomm_of, args=args)
        return t
    if nr_threads == 1: # debug
        compute_dfcomm_of(0, unique_pid)
        df['comm'] = df_comm
        return comm
    print('Spawning {} threads'.format(nr_threads))
    threads = [spawn(tid) for tid in range(nr_threads)]
    print('Starting threads')
    for t in threads:
        t.start()
    print('Joining threads')
    for t in threads:
        t.join()
    df['comm'] = df_comm
    return comm
def load_tracer_raw(path):
    data = {
        cpu : load_tracer_raw_per_cpu(os.path.join(path, cpu))
        for cpu in os.listdir(path)
    }
    cpus = list(data.keys())
    cpus.sort(key=lambda x:int(x))
    keys = list(data[cpus[0]].keys())
    df = {
	k : np.concatenate([data[cpu][k] for cpu in cpus])
	for k in keys
    }
    df['cpu'] = np.concatenate([np.array([int(cpu)]*len(data[cpu][keys[0]])) for cpu in cpus])
    df = pd.DataFrame(df)
    df.sort_values(by='timestamp', inplace=True)
    df.index = np.arange(len(df))
    comm = compute_dfcomm(df)
    return df, comm

def load_tracer_raw_per_cpu(path):
    data = {
        'timestamp' : [],
        'pid' : [],
        'event' : [],
        'addr' : [],
        'arg0' : [],
        'arg1' : [],
    }
    N = 8+4+4+8
    with open(path, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        assert(len(mm)%N == 0)
        for i in range(len(mm)//N):
            entry = mm[i*N:(i+1)*N]
            head = entry[:16]
            tail = entry[16:]
            timestamp, pid, event = struct.unpack('<Qii',head)
            arg0, arg1 = struct.unpack('<ii',tail)
            addr = (arg0<<32|arg1)
            entry = {
                'timestamp' : timestamp,
                'pid' : pid,
                'event' : event,
                'addr' : addr,
                'arg0' : arg0,
                'arg1' : arg1,
            }
            for k in entry:
                data[k].append(entry[k])
    return data

def store(grp, obj):
    for key in obj:
        if isinstance(obj[key], (dict, pd.DataFrame)):
            new_grp = grp.create_group(key)
            store(new_grp, obj[key])
        elif isinstance(obj[key], (str,int,float)):
            grp.attrs[key] = obj[key]
        elif isinstance(obj[key], (np.ndarray,list)):
            grp.create_dataset(key,data=obj[key],compression="gzip")
        elif isinstance(obj[key], (pd.Series)):
            grp.create_dataset(key,data=np.array(obj[key]),compression="gzip")
        else:
            raise Exception('Cannot store key {} (type={}) of obj {}'.format(key,type(obj[key]),obj))

if __name__ == '__main__':
    main()
