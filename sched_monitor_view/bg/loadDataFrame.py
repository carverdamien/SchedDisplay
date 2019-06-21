from threading import Thread
import h5py
import numpy as np
import pandas as pd

def bg(*args):
	return Thread(target=fg, args=args)

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
	callback(path, df, done)
