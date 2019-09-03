# NOTE that pandas is NOT used here
# Refrain from using pandas
import tarfile, os, shutil
import numpy as np
from threading import Thread
import time

def from_tar(path, only=None):
	dd = {}
	with tarfile.open(path, 'r') as tar:
		#
		# TODO: write a pragma parallel decorator
		#
		def filter(tarinfo, only=None):
			if only is None:
				return tarinfo.isreg() and os.path.splitext(tarinfo.name)[1] == '.npz'
			elif isinstance(only, list):
				return filter(tarinfo) and os.path.splitext(os.path.basename(tarinfo.name))[0] in only
			else:
				raise Exception('Exception: only must be None or list')
		def target(tarinfo):
			start = time.time()
			with tarfile.open(path, 'r') as tar:
				with tar.extractfile(tarinfo.name) as f:
					npzfile = np.load(f)
					dd.update({k:npzfile[k] for k in npzfile.files})
			end = time.time()
			print('{} loaded in {} s'.format(tarinfo.name, end-start))
		def spawn(tarinfo):
			args = (tarinfo,)
			t = Thread(target=target, args=args)
			t.start()
			return t
		thread = [spawn(tarinfo) for tarinfo in tar if filter(tarinfo, only)]
		for t in thread: t.join()
	return dd

def walk_data(data, k, func_data):
	for myk in data.keys():
		v = data[myk]
		if isinstance(v, dict):
			walk_data(v, k+[myk], func_data)
		else:
			func_data(list(k+[myk]), v)

def add_array_to_tar(path, k, v):
	if isinstance(k, str):
		k = [k]
	with tarfile.open(path, 'a') as tar:
		k = ['data']+k
		d = '/'.join(k[:-1])
		if not os.path.isdir(d):
			os.makedirs(d)
		fname = '{}.npz'.format('/'.join(k))
		np.savez_compressed(fname, **{k[-1]:v})
		tar.add(fname)
		os.remove(fname)
		shutil.rmtree('data')

def to_tar(path, dd):
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
		walk_data(dd,[],func_data)
		shutil.rmtree('data')