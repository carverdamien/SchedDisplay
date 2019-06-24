from threading import Thread
import h5py
import numpy as np
import pandas as pd
import itertools

EXEC_EVT = 0

def bg(*args):
	return Thread(target=fg, args=args)

# TODO: modify report.py to match the DataFrame format
def fg(path, path_id, callback, done):
	data = {}
	with h5py.File(path) as f:
		dataset = f['sched_monitor']['tracer-raw']
		for cpu in dataset.keys():
			data[cpu] = {
				k : np.array(dataset[cpu][k])
				for k in dataset[cpu].keys()
			}
		tmin = min([data[cpu]['timestamp'][0] for cpu in data])
		for cpu in data:
			data[cpu]['timestamp']-=tmin
	cpus = list(data.keys())
	cpus.sort(key=lambda x:int(x))
	keys = list(data[cpus[0]].keys())
	df = {
		k : np.concatenate([data[cpu][k] for cpu in cpus])
		for k in keys
	}
	df['cpu'] = np.concatenate([np.array([int(cpu)]*len(data[cpu][keys[0]])) for cpu in cpus])
	df['path_id'] = np.array([path_id]*len(df['cpu']))
	df = pd.DataFrame(df)
	df['comm'] = np.array(['']*len(df))
	sel = df['event'] == EXEC_EVT
	for pid, arg0, arg1 in itertools.zip_longest(df['pid'][sel], df['arg0'][sel], df['arg1'][sel]):
		sel = df['pid'] == pid
		arg0 = int(arg0)
		arg1 = int(arg1)
		b = (arg0<<32|arg1).to_bytes(8, byteorder="little")
		i = 0
		while i < 7 and b[i] > 0:
			i+=1
		comm = b[:i].decode()
		print(pid, b, comm)
		df.loc[sel, 'comm'] = comm
	callback(path, df, done)
