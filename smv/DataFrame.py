import tarfile, os, shutil
import numpy as np
import pandas as pd
from threading import Thread
import time

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

def DataFrame(path):
	df = {}
	with tarfile.open(path, 'r') as tar:
		def target(tarinfo):
			start = time.time()
			with tarfile.open(path, 'r') as tar:
				with tar.extractfile(tarinfo.name) as f:
					npzfile = np.load(f)
					df.update({k:npzfile[k] for k in npzfile.files})
			end = time.time()
			print('{} loaded in {} s'.format(tarinfo.name, end-start))
		def spawn(tarinfo):
			args = (tarinfo,)
			t = Thread(target=target, args=args)
			t.start()
			return t
		thread = [spawn(tarinfo) for tarinfo in tar if tarinfo.isreg() and os.path.splitext(tarinfo.name)[1] == '.npz']
		for t in thread: t.join()
	df = pd.DataFrame(df)
	return df

def walk_data(data, k, func_data):
	for myk in data.keys():
		v = data[myk]
		if isinstance(v, dict):
			walk_data(v, k+[myk], func_data)
		else:
			func_data(list(k+[myk]), v)

def save(path, df):
	with tarfile.open(path, 'w') as tar:
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
		walk_data(df,[],func_data)
		shutil.rmtree('data')