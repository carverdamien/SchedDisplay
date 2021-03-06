import numpy as np
import pandas as pd
from threading import Thread, Lock
from multiprocessing import cpu_count, Semaphore
import traceback, tarfile, json, parse, os, itertools

def parallel(iter_args, sem_value=cpu_count()):
	def wrap(func):
		def f():
			sem = Semaphore(sem_value)
			def target(*args):
				sem.acquire()
				func(*args)
				sem.release()
			def spawn(*args):
				t = Thread(target=target, args=args)
				t.start()
				return t
			threads = [spawn(*args) for args in iter_args]
			for t in threads:
				t.join()
		return f
	return wrap

class ColumnNotFoundException(Exception):
	pass

FLOAT = float
STRING = str

class Column(object):
	"""docstring for Column"""
	def __init__(self, *args, **kwargs):
		super(Column, self).__init__()
		self.dtype = kwargs['dtype']
		if self.dtype == FLOAT:
			self.default = kwargs.get('default', np.NaN)
		elif self.dtype == STRING:
			self.default = kwargs.get('default', '(NULL)')
		else:
			raise Exception(f'{self.dtype} unsupported')
		self.function = kwargs['function']
		self.name = kwargs.get('name', self.function.__name__)
	def __call__(self, index, row):
		try:
			return self.dtype(self.function(index, row))
			# return self.function(index, row)
		except ColumnNotFoundException as e:
			return self.default
		except Exception as e:
			print(traceback.format_exc())
			# raise e
			return self.default

class TableModel(object):
	"""docstring for AbstractTableModel"""
	def __init__(self, *args, **kwargs):
		super(TableModel, self).__init__()
		self.__index = kwargs.get('index')
		self.__path = kwargs.get('path',f'./examples/cache/{self.__class__.__name__}')
		self.__df = None
		self.__lock = Lock()
		self.__columns = []
		self.__thread = None

	"""Decorator"""

	def lock(function):
		def f(self, *args, **kwargs):
			r = None
			if not self.__lock.acquire(False):
				raise Exception(f'Fail to acquire self.__lock in {function.__name__}')
			try:
				r = function(self, *args, **kwargs)
			except Exception as e:
				self.__lock.release()
				print(traceback.format_exc())
				raise e
			self.__lock.release()
			return r
		f.__name__ = function.__name__
		return f

	"""Public"""

	@lock
	def add_column(self, c):
		if not isinstance(c, Column):
			raise Exception(f'{c} is not {Column}')
		self.__columns.append(c)

	@property
	def df(self):
		if self.__df is None:
			self.__build()
		return self.__df

	@lock
	def columns_name(self):
		return [c.name for c in self.__columns]

	@lock
	def empty_df(self):
		return self.allocate_df(0)

	@lock
	def load(self, path=None):
		if path is None:
			path = self.__path
		self.__df = pd.read_parquet(path)

	def save(self, path=None):
		if path is None:
			path = self.__path
		self.df.to_parquet(path, compression='UNCOMPRESSED')

	def build(self, callback, force=True):
		def target():
			try:
				if force:
					self.__build()
				callback(self.df)
			except Exception as e:
				print(traceback.format_exc())
		self.__thread = Thread(target=target)
		self.__thread.start()

	def stream(self, callback, batch=1):
		def target():
			try:
				self.__stream(callback, batch)
			except Exception as e:
				print(traceback.format_exc())
		self.__thread = Thread(target=target)
		self.__thread.start()

	def join(self):
		self.__thread.join()

	""""Private"""

	@lock
	def __build(self):
		index = self.__index()
		self.__df = self.__rows(index)

	@lock
	def __stream(self, callback, batch=1):
		index = self.__index()
		concat = []
		N = len(index)
		for i in range(0, N, batch):
			df = self.__rows(index[i:min(N,i+batch)])
			callback(df)
			concat.append(df)
		self.__df = pd.concat(concat, ignore_index=True)

	def allocate_df(self, n):
		return pd.DataFrame({
			c.name : (np.array([np.NaN]*n, dtype=c.dtype) if c.dtype != STRING else np.array(['(NULL)']*n, dtype=c.dtype))
			for c in self.__columns
		})

	def __rows(self, index):
		N = len(index)
		df = self.allocate_df(N)
		for i in range(N):
			for c in self.__columns:
				df.loc[i, c.name] = c(index[i], df.iloc[i])
		# TODO: in parallel. The following does not realy improves
		#@parallel(itertools.product(range(N)))
		#def compute_row(i):
		#	for c in self.__columns:
		#		df.loc[i,c.name] = c(index[i], df.iloc[i])
		#compute_row()
		return df

def parsable_column(dtype, name, basename, pattern):
	def function(i, r):
		try:
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
		except Exception as e:
			# print(traceback.format_exc())
			pass
		raise ColumnNotFoundException()
	function.__name__ = name
	return Column(dtype=dtype, function=function)

def json_column(dtype, name, basename, keys):
	def function(i, r):
		try:
			with tarfile.open(i, 'r:') as tar:
				for tarinfo in tar:
					if os.path.basename(tarinfo.name) != basename:
						continue
					with tar.extractfile(tarinfo.name) as f:
						value = json.load(f)
						for k in keys:
							value = value[k]
						return value
					break
		except Exception as e:
			# print(traceback.format_exc())
			pass
		raise ColumnNotFoundException()
	function.__name__ = name
	return Column(dtype=dtype, function=function)

""" Test """

def test():
	def find_files(directory, ext, regexp=".*"):
		import re
		regexp = re.compile(regexp)
		for root, dirs, files in os.walk(directory, topdown=False):
			for name in files:
				path = os.path.join(root, name)
				if ext == os.path.splitext(name)[1] and regexp.match(path):
					yield path
	def index():
		return sorted(list(find_files('./examples/trace', '.tar', '.*phoronix.*')))
	tm = TableModel(index=index)
	COLUMNS = [
		[FLOAT, 'usr_bin_time',  'time.err', '{pattern:F}'],
		[FLOAT, 'sysbench_trps', 'run.out',  '{:s}transactions:{:s}{:d}{:s}({pattern:F} per sec.)'],
	]
	for i in range(4):
		COLUMNS.extend([
			[FLOAT, 'cpu%d_package_joules'%(i), 'cpu-energy-meter.out',  'cpu%d_package_joules={pattern:F}'%(i)],
			[FLOAT, 'cpu%d_dram_joules'%(i), 'cpu-energy-meter.out',  'cpu%d_dram_joules={pattern:F}'%(i)],
		])
	for args in COLUMNS:
		tm.add_column(parsable_column(*args))
	MAX_PHORONIX = 2
	PHORONIX_TEST = [
		[STRING, f'phoro_test{i}', 'phoronix.json', ['results',i,'test']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX_ARGS = [
		[STRING, f'phoro_args{i}', 'phoronix.json', ['results',i,'arguments']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX_UNITS = [
		[STRING, f'phoro_units{i}', 'phoronix.json', ['results',i,'units']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX_VALUE = [
		[FLOAT, f'phoro_value{i}', 'phoronix.json', ['results',i,'results','schedrecord','value']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX = [i for j in itertools.zip_longest(PHORONIX_TEST,PHORONIX_ARGS,PHORONIX_UNITS,PHORONIX_VALUE) for i in j]
	JSONS = PHORONIX
	for args in JSONS:
		tm.add_column(json_column(*args))
	TOTAL_ENERGY = [
		[FLOAT, 'total_package_joules',lambda index, row: np.sum([row['cpu%d_package_joules'%(i)] for i in range(4)])],
		[FLOAT, 'total_dram_joules',   lambda index, row: np.sum([row['cpu%d_dram_joules'%(i)] for i in range(4)])],
		[FLOAT, 'total_joules',        lambda index, row: np.sum([row[c] for c in ['total_package_joules', 'total_dram_joules']])],
	]
	for args in TOTAL_ENERGY:
		kwargs = {'dtype':args[0],'name':args[1],'function':args[2]}
		tm.add_column(Column(**kwargs))
	#print(tm.df)
	def callback(foo):
		print(foo)
	tm.stream(callback)
	tm.join()
	print(tm.df)

if __name__ == '__main__':
	test()
