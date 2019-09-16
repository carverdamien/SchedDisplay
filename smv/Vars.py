import tarfile, os
FUNC = []

def from_tar(path):
	d={}
	for f in FUNC:
		d.update(f(path))
	return d

def add(function):
	def f(*args, **kwargs):
		try:
			return function(*args, **kwargs)
		except Exception as e:
			print(e)
		return {}
	f.__name__ = function.__name__
	FUNC.append(f)
	return f

@add
def parse_sched_monitor_events(path):
	d = {}
	with tarfile.open(path, 'r') as tar:
		for tarinfo in tar:
			if os.path.basename(tarinfo.name) != 'sched_monitor_events.start':
				continue
			with tar.extractfile(tarinfo.name) as f:
				for line in f.read().decode().split('\n'):
					if len(line) == 0:
						break
					value, key = line.split(' ')
					d[key] = value
			break
	return d
