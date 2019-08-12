#!/usr/bin/env python3

from smv.DataFrame import DataFrame
import time, sys, tarfile, json, io, os
import numpy as np
from threading import Thread

def log(func):
	def f(*args, **kwargs):
		start = time.time()
		print('{} starts at {}'.format(func.__name__, start))
		r = func(*args, **kwargs)
		end = time.time()
		print('{} took {} s'.format(func.__name__, end - start))
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
def main():
	_, hdf5, tar = sys.argv
	df = load_DataFrame(hdf5)
	convert(tar, df)
	df = load_tar(tar)
	print(df)
	pass

if __name__ == '__main__':
	main()
