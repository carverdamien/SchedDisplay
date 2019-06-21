STATE = {}

TODO = []

def hdf5_is_loaded(path):
	return path in TODO
def load_hdf5(path):
	TODO.append(path)
def unload_hdf5(path):
	TODO.remove(path)