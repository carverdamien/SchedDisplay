from threading import Thread
import h5py
import numpy as np

def load(path, callback):
	args=(path, callback)
	return Thread(target=target, args=args)

def target(path, callback):
	data = {}
	with h5py.File(path) as f:
		dataset = f['sched_monitor']['tracer-raw']
		for cpu in dataset.keys():
			data[cpu] = {
				k : np.array(dataset[cpu][k])
				for k in dataset[cpu].keys()
			}
	callback(path, data)
