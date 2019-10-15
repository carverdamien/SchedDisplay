# NOTE that pandas is NOT used here
# Refrain from using pandas
import tarfile, os, shutil
import numpy as np
from threading import Thread
import time
from smv.Computable import COMPUTABLE

def from_tar(path, only=None, compute=None, log=print):
	if only is not None:
		log('only is deprecated, use compute instead')
	if compute is not None:
		compute = {k:COMPUTABLE[k] for k in compute if k in COMPUTABLE}
	dd = {}
	with tarfile.open(path, 'r:') as tar:
		#
		# TODO: write a pragma parallel decorator
		#
		def filter(tarinfo, only=None, compute=None):
			if only is None or compute is None:
				return tarinfo.isreg() and os.path.splitext(tarinfo.name)[1] == '.npz'
			elif isinstance(compute, dict):
				return filter(tarinfo) and os.path.splitext(os.path.basename(tarinfo.name))[0] in compute
			elif isinstance(only, list):
				return filter(tarinfo) and os.path.splitext(os.path.basename(tarinfo.name))[0] in only
			else:
				raise Exception('Exception: wrong type: only|compute')
		def target(tarinfo):
			start = time.time()
			with tarfile.open(path, 'r:') as tar:
				with tar.extractfile(tarinfo.name) as f:
					npzfile = np.load(f)
					dd.update({k:npzfile[k] for k in npzfile.files})
			end = time.time()
			log('{} loaded in {} s'.format(tarinfo.name, end-start))
		def spawn(tarinfo):
			args = (tarinfo,)
			t = Thread(target=target, args=args)
			t.start()
			return t
		thread = [spawn(tarinfo) for tarinfo in tar if filter(tarinfo, only, compute)]
		for t in thread: t.join()
	if compute is not None:
		for k in compute:
			if k in dd:
				log(f'{k} was previously computed and cached in {path}')
				continue
			dd[k] = compute[k](dd, log=log)
			# TODO: flock path
			# add_array_to_tar(path, k, dd[k])
			# funlock path
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