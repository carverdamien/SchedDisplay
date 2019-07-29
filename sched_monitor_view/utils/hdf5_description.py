#!/usr/bin/env python3
import h5py, sys
f=h5py.File(sys.argv[1], 'r')

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
print('\n'.join(description(f)))
