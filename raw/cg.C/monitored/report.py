#!/usr/bin/env python3
import sys, h5py, os, mmap, struct, json, itertools
import numpy as np
import pandas as pd

EXEC_EVT = 0

def main():
    o_path, i_path = sys.argv[1:3]
    data = load_data(i_path)
    with h5py.File(o_path, 'w') as f:
        store(f, data)

def load_data(path):
    return {
        'summary' : load_json(os.path.join(path, 'summary.json')),
        'sched_monitor' : load_sched_monitor(os.path.join(path,'sched_monitor')),
    }

def load_json(path):
    with open(path) as f:
        return json.load(f)

def load_sched_monitor(path):
    return {
        'tracer-raw' : load_tracer_raw(os.path.join(path, 'tracer-raw')),
    }

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
    df['comm'] = np.chararray(np.shape((len(df))), itemsize=9)
    df['comm'] = ''
    sel = df['event'] == EXEC_EVT
    it = itertools.zip_longest(
        df['pid'][sel],
        df['addr'][sel],
        df['timestamp'][sel],
    )
    for pid, addr, timestamp in it:
        sel = (df['pid'] == pid) & (df['timestamp'] >= timestamp)
        b = addr.to_bytes(8, byteorder="little")
        i = 0
        while i < 8 and b[i] > 0:
            i+=1
        comm = b[:i].decode()
        df.loc[sel, 'comm'] = comm
    return df

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
