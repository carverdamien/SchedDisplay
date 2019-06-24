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
		dataset = f['sched_monitor']['tracer-raw']
		keys = list(dataset.keys())
		df = {
			k : np.array(dataset[k])
			for k in keys
		}
		df['timestamp']-=min(df['timestamp'])
		df['path_id'] = np.array([path_id]*len(df['timestamp']))
		df = pd.DataFrame(df)
		df['comm'] = df['comm'].str.decode("utf-8")
		callback(path, df, done)
