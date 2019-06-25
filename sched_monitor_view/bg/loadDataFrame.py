from threading import Thread
import h5py
import numpy as np
import pandas as pd
import itertools

EXEC_EVT = 0

def bg(*args):
	return Thread(target=fg, args=args)

def fg(path, path_id, callback, done):
	df = {}
	with h5py.File(path) as f:
		comm = f['sched_monitor']['tracer-raw']['comm'].attrs
		comm = {k:comm[k] for k in comm.keys()}
		dataset = f['sched_monitor']['tracer-raw']['df']
		keys = list(dataset.keys())
		df = {
			k : np.array(dataset[k])
			for k in keys
		}
		df['timestamp']-=min(df['timestamp'])
		df['path_id'] = np.array([path_id]*len(df['timestamp']))
		df = pd.DataFrame(df)
		data = {
			'df' : df,
			'comm' : comm,
		}
		callback(path, data, done)
