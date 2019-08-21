#!/usr/bin/env python3

import time, sys, tarfile, json, io, os, shutil
import numpy as np
from threading import Thread

import h5py
import numpy as np
import pandas as pd

def walk_hdf5(f, k, func_attr, func_grp):
	for myk in f.attrs.keys():
		v = f.attrs[myk]
		func_attr(list(k+[myk]), v)
	for myk in f.keys():
		v = f[myk]
		if isinstance(v, h5py._hl.group.Group):
			walk_hdf5(v, k+[myk], func_attr, func_grp)
		else:
			func_grp(list(k+[myk]), v)

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

def log(func):
	def f(*args, **kwargs):
		start = time.time()
		print('{}({}) starts at {}'.format(func.__name__, str(args), start))
		r = func(*args, **kwargs)
		end = time.time()
		print('{}({}) took {} s'.format(func.__name__, str(args), end - start))
		return r
	return f

@log
def load_DataFrame(path):
	with open(path, 'rb') as f:
		return DataFrame(f)

@log
def convert(path, df):
	with tarfile.open(path, 'w') as tar:
		for k in df.columns:
			fname = '{}.npz'.format(k)
			np.savez_compressed(fname, **{k:df[k]})
			tar.add(fname)
			os.remove(fname)
	pass

@log
def load_tar(path):
	df = {}
	with tarfile.open(path, 'r') as tar:
		@log
		def target(tarinfo):
			with tarfile.open(path, 'r') as tar:
				with tar.extractfile(tarinfo.name) as f:
					npzfile = np.load(f)
					df.update({k:npzfile[k] for k in npzfile.files})
		def spawn(tarinfo):
			args = (tarinfo,)
			t = Thread(target=target, args=args)
			t.start()
			return t
		thread = [spawn(tarinfo) for tarinfo in tar if tarinfo.isreg()]
		for t in thread: t.join()
	return df

@log
def load_any_hdf5(hdf5):
	with h5py.File(hdf5, 'r') as f:
		state = {'meta':{},'data':{}}
		def func_attr(k,v):
			it = state['meta']
			# print(k)
			while(len(k)>1):
				if k[0] not in it:
					it[k[0]] = {}
				it = it[k[0]]
				k.pop(0)
			it[k[0]]=v
			# print(state)
		def func_grp(k,v):
			it = state['data']
			print(k)
			while(len(k)>1):
				if k[0] not in it:
					it[k[0]] = {}
				it = it[k[0]]
				k.pop(0)
			it[k[0]]=np.array(v)
			# print(state)
			pass
		walk_hdf5(f,[],func_attr,func_grp)
		return state

def default(o):
	print(o, int(o))
	if isinstance(o, np.int64): return int(o)
	raise TypeError

@log
def to_tar(path, state):
	with tarfile.open(path, 'w') as tar:
		with open('meta.json','w') as f:
			json.dump(state['meta'], f, default=default)
		tar.add('meta.json')
		os.remove('meta.json')
		def func_data(k,v):
			print(k,v)
			k = ['data']+k
			d = '/'.join(k[:-1])
			if not os.path.isdir(d):
				os.makedirs(d)
			fname = '{}.npz'.format('/'.join(k))
			np.savez_compressed(fname, **{k[-1]:v})
			tar.add(fname)
			os.remove(fname)
			pass
		walk_data(state['data'],[],func_data)
		shutil.rmtree('data')

def walk_data(data, k, func_data):
	for myk in data.keys():
		v = data[myk]
		if isinstance(v, dict):
			walk_data(v, k+[myk], func_data)
		else:
			func_data(list(k+[myk]), v)

@log
def main():
	_, hdf5, tar = sys.argv
	state = (hdf5)
	to_tar(tar, state)
	# df = load_DataFrame(hdf5)
	# convert(tar, df)
	# df = load_tar(tar)
	# print(df)
	pass

if __name__ == '__main__':
	main()
