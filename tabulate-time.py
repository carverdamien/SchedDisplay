#!/usr/bin/env python3
import tabulate, sys, h5py, os

def get_completion_time(hdf5):
	with h5py.File(hdf5, 'r') as f:
		return f['summary'].attrs['time']

def parse_stdin(f):
	return [[f(a) for a in line.split(' ')] for line in sys.stdin]

def foo(a):
	hdf5 = a.strip()
	if os.path.exists(hdf5):
		try:
			return get_completion_time(hdf5)
		except Exception as e:
			print(e)
	return a

table = parse_stdin(foo)
print(tabulate.tabulate(table))
