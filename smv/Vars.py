import tarfile, os, string
FUNC = []

class Vars(object):
	"""docstring for Vars"""
	def __init__(self, vars):
		super(Vars, self).__init__()
		self.vars = vars
	
	def parse(self, o):
		if isinstance(o, dict):
			for k in o:
				o[k] = self.parse(o[k])
		elif isinstance(o, list):
			for i in range(len(o)):
				o[i] = self.parse(o[i])
		elif isinstance(o, str):
			t = string.Template(o)
			o = t.substitute(**self.vars)
		else:
			pass
		return o

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

# DEPRECATED
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

@add
def parse_sched_log_traced_events(path):
	d = {}
	with tarfile.open(path, 'r') as tar:
		for tarinfo in tar:
			if os.path.basename(tarinfo.name) != 'sched_log_traced_events.start':
				continue
			with tar.extractfile(tarinfo.name) as f:
				for line in f.read().decode().split('\n'):
					if len(line) == 0:
						break
					value, key = line.split(' ')
					d[key] = value
			break
	return d
