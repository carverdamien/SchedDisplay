import pandas as pd
import dask
from multiprocessing import cpu_count
import numpy as np
import time
from smv.ConsoleViewController import logFunctionCall

def default_log(*args):
	pass

def debug(func):
	def f(*args, **kwargs):
		fname = func.__name__
		print('{}({},{}) starts'.format(fname,args,kwargs))
		starts = time.time()
		try:
			r = func(*args,**kwargs)
		except Exception as e:
			print('Exception',type(e),e)
			raise e
		ends = time.time()
		print('{} ends in {}s and returns {}'.format(fname, ends-starts, r))
		return r
	return f

# @debug
def query(df, q):
	assert isinstance(q, str), "q={} is not str".format(q)
	return df.query(q)

# @debug
def assign(df, key, value):
	assert isinstance(key, str), "key={} is not str".format(key)
	return df.assign(**{key:apply(df,value)})

# @debug
def add(df, *args):
	args = list(args)
	INSTANCE=(int, float, np.ndarray, pd.Series)
	for i in range(len(args)):
		if not isinstance(args[i], INSTANCE):
			args[i] = apply(df, args[i])
		assert isinstance(args[i], INSTANCE), "{} is not good type".format(args[i])
	s = args[0]
	for a in args[1:]:
		s += a
	return s

OP = {
	'query':query,
	'=':assign,
	'+':add,
}

# @debug
def apply(df, op):
	if isinstance(op, list):
		op, args = op[0], op[1:]
		if op not in OP:
			raise Exception('{} not in {}'.format(op, OP))
		return OP[op](df, *args)
	elif isinstance(op, str):
		return df[op]
	elif isinstance(op, (int, float)):
		r = np.empty(len(df),dtype=type(op))
		r[:] = op
		return r
	else:
		raise Exception('Cannot handle {}'.format(op))

# @debug
def one(df, i, operators, shape, log=default_log):
	for op in operators:
		log('Processing {}'.format(op))
		df = apply(df, op)
	return df.assign(c=i)[shape]

# @debug
def category(df, i, config, log=default_log):
	shape = config['shape']
	c = config['c'][i]
	log('Processing {}'.format(c))
	return pd.concat([one(df, i, o, shape, log=log) for o in c['concatenate']])

def from_df(df, config, log=default_log):
	@logFunctionCall(log)
	def subtract_min_timestamp(df):
		# return df['timestamp']-min(df['timestamp'])
		t0 = df['timestamp'][0]
		df['timestamp'] -= t0
		return df['timestamp']
	df['timestamp'] = subtract_min_timestamp(df)
	@logFunctionCall(log)
	def array_to_dataframe(df):
		return pd.DataFrame(df)
	df = array_to_dataframe(df)
	@logFunctionCall(log)
	def compute_categories(df, config):
		return [
			category(df, i, config, log=log)
			for i in range(len(config['c']))
		]
	concat = compute_categories(df, config)
	for i in range(len(concat)):
		n = len(concat[i])
		log('{} elements in category[{}]'.format(n,i))
		config['c'][i]['len'] = n
	@logFunctionCall(log)
	def concatenate_categories(concat):
		return pd.concat(concat)
	df = concatenate_categories(concat)
	@logFunctionCall(log)
	def convert_c_as_CategoricalDtype(df):
		df['c'] = df['c'].astype(pd.CategoricalDtype(ordered=True))
		return df
	df = convert_c_as_CategoricalDtype(df)
	@logFunctionCall(log)
	def dask_partition(df):
		df = dask.dataframe.from_pandas(df, npartitions=cpu_count())
		df.persist() # Persist multiple Dask collections into memory
		return df
	return dask_partition(df)
