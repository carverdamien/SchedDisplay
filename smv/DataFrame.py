import h5py
import numpy as np
import pandas as pd

def description(f):
	res = []
	for k in f.attrs.keys():
		v = f.attrs[k]
		res.append('{}: {}'.format(k, v))
	for k in f.keys():
		v = f[k]
		res.append('{}: {}'.format(k,v))
		if isinstance(v, h5py._hl.group.Group):
			res+=description(v)
	return res

def DataFrame(io):
	with h5py.File(io, 'r') as f:
		perf_event = {}
		if 'perf_event' in f:
			perf_event = f['perf_event']
			perf_event = {
				k : {
					kk : perf_event[k].attrs[kk]
					for kk in  perf_event[k].attrs.keys()
				}
				for k in perf_event.keys()
			}
		comm = f['sched_monitor']['tracer-raw']['comm'].attrs
		comm = {k:comm[k] for k in comm.keys()}
		dataset = f['sched_monitor']['tracer-raw']['df']
		keys = list(dataset.keys())
		df = {
			k : np.array(dataset[k])
			for k in keys
		}
		df['timestamp']-=min(df['timestamp'])
		# df['path_id'] = np.array([path_id]*len(df['timestamp']))
		df = pd.DataFrame(df)
		data = {
			'description' : description(f),
			'df' : df,
			'comm' : comm,
			'perf_event' : perf_event,
		}
		return df