import numpy as np
import pandas as pd
import parse, os, traceback, tarfile
from threading import Thread, Lock

class Column(object):
	"""docstring for Column"""
	def __init__(self, *args, **kwargs):
		super(Column, self).__init__()
		self.dtype = kwargs['dtype']
		if self.dtype != str:
			def undefined(i):
				return np.NaN
		else:
			def undefined(i):
				return i
		self.function = kwargs.get('function', undefined)
		self.name = kwargs.get('name', self.function.__name__)
	def __call__(self, i):
		return self.function(i)

# TODO:
# write TableModel
# make class TracesModel(TableModel)
# add notification

class TracesModel(object):
	"""docstring for TracesModel"""
	def __init__(self, *args, **kwargs):
		super(TracesModel, self).__init__()
		self.directory = kwargs.get('directory', './examples/trace/')
		self.cache = kwargs.get('cache', './examples/cache/traces.parquet')
		self.index = []
		self.columns = []
		self.df = pd.DataFrame({})
		self.lock = Lock()
		self.thread = None

	def lockfunc(function):
		def f(self, *args, **kwargs):
			r = None
			if not self.lock.acquire(False):
				raise Exception('Fail to acquire self.lock in f{function.__name__}')
			try:
				r = function(self, *args, **kwargs)
			except Exception as e:
				print(traceback.format_exc())
				pass
			finally:
				self.lock.release()
			return r
		f.__name__ = function.__name__
		return f

	@lockfunc
	def add_column(self, c):
		if not isinstance(c, Column):
			raise Exception(f'{c} is not {Column}')
		self.columns.append(c)

	@lockfunc
	def columns_name(self):
		return [c.name for c in self.columns]

	def _build_index(self):
		self.index.clear()
		self.index.extend(sorted(list(find_files(self.directory, '.tar'))))

	def _init_df(self):
		self.df = pd.DataFrame({
			c.name : (np.array([], dtype=c.dtype) if c.dtype != str else [])
			for c in self.columns
		})

	def _concat(self, df):
		self.df = pd.concat([self.df, df], ignore_index=True)

	def _rows(self, index):
		return {
			c.name : (np.array([c(i) for i in index], dtype=c.dtype) if c.dtype != str else [c(i) for i in index])
			for c in self.columns
		}

	@lockfunc
	def _build(self):
		self._build_index()
		self._init_df()
		self._concat(pd.DataFrame(self._rows(self.index)))
		return self.df

	@lockfunc
	def _stream(self, callback, batch):
		self._build_index()
		self._init_df()
		N = len(self.index)
		for i in range(0,N,batch):
			index = self.index[i:min(i+batch,N)]
			df = pd.DataFrame(self._rows(index))
			self._concat(df)
			callback(df)

	def build(self, callback=None):
		if callback is None:
			return self._build()
		else:
			def target():
				callback(self._build())
			self.thread = Thread(target=target)
			self.thread.start()
			return None

	def stream(self, callback, batch=1):
		if batch <= 0:
			self.build(callback=callback)
		else:
			def target():
				self._stream(callback, batch)
			self.thread = Thread(target=target)
			self.thread.start()

	def join(self):
		self.thread.join()

	@lockfunc
	def save(self):
		print(self.df)
		self.df.to_parquet(self.cache, compression='UNCOMPRESSED')

	@lockfunc
	def load(self):
		self.df = pd.read_parquet(self.cache)

def find_files(directory, ext):
	for root, dirs, files in os.walk(directory, topdown=False):
		for name in files:
			path = os.path.join(root, name)
			if ext == os.path.splitext(name)[1]:
				yield path

def parsable_column(dtype, name, basename, pattern):
	def function(i):
		with tarfile.open(i, 'r:') as tar:
			for tarinfo in tar:
				if os.path.basename(tarinfo.name) != basename:
					continue
				with tar.extractfile(tarinfo.name) as f:
					re = parse.compile(pattern)
					for line in f.read().decode().split('\n'):
						r = re.parse(line)
						if r is not None:
							return r.named['pattern']
				break
		return np.NaN
	function.__name__ = name
	return Column(dtype=dtype, function=function)

def test():
	traces = TracesModel()
	def fname(i):
		return i
	traces.add_column(Column(dtype=str, function=fname))
	traces.build()
	def callback(df):
		print(f"{len(df)}")
	traces.build(callback=callback)
	traces.join()
	traces.save()
	traces.load()
	print(traces.df)
	COLUMNS = [
		[float, 'usr_bin_time',  'time.err', '{pattern:F}'],
		[float, 'sysbench_trps', 'run.out',  '{:s}transactions:{:s}{:d}{:s}({pattern:F} per sec.)'],
	]
	for i in range(4):
		COLUMNS.extend([
			[float, 'cpu%d_package_joules'%(i), 'cpu-energy-meter.out',  'cpu%d_package_joules={pattern:F}'%(i)],
			[float, 'cpu%d_dram_joules'%(i), 'cpu-energy-meter.out',  'cpu%d_dram_joules={pattern:F}'%(i)],
		])
	for args in COLUMNS:
		traces.add_column(parsable_column(*args))
	shared = {}
	def callback(row):
		if 'df' in shared:	
			shared['df'] = pd.concat([shared['df'], row], ignore_index=True)
		else:
			shared['df'] = row
		print(row)
	traces.stream(callback)
	traces.join()
	print(shared)
	pass

if __name__ == '__main__':
	test()
