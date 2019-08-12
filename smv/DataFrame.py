import tarfile, os
import numpy as np
import pandas as pd
from threading import Thread

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
			with tarfile.open(path, 'r') as tar:
				with tar.extractfile(tarinfo.name) as f:
					npzfile = np.load(f)
					df.update({k:npzfile[k] for k in npzfile.files})
		def spawn(tarinfo):
			args = (tarinfo,)
			t = Thread(target=target, args=args)
			t.start()
			return t
		thread = [spawn(tarinfo) for tarinfo in tar if tarinfo.isreg() and os.path.splitext(tarinfo.name)[1] == '.npz']
		for t in thread: t.join()
	df = pd.DataFrame(df)
	return df
