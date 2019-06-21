from threading import Thread
import h5py
import numpy as np

def bg(*args):
	return Thread(target=fg, args=args)

def fg(path, callback, done):
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
	callback(path, data, done)
