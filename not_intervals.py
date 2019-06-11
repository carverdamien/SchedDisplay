#!/usr/bin/env python3
import numpy as np
import sys, h5py

o_path, i_path = sys.argv[1:]

def not_data(data):
    inf, sup = data
    new_inf = sup[:-1]
    new_sup = inf[1:]
    return np.array([new_inf, new_sup])

with h5py.File(i_path, 'r') as i:
    data = [np.array(i[cpu]) for cpu in sorted(list(i.keys()), key=lambda e:int(e))]
    data = [not_data(d) for d in data]
    with h5py.File(o_path, 'w') as o:
        for cpu in range(len(data)):
            o.create_dataset(str(cpu),data=data[cpu],compression="gzip",dtype='i8')
