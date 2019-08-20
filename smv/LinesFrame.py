import pandas as pd
import dask
from multiprocessing import cpu_count
import numpy as np
import time

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
def one(df, operators):
	for op in operators:
		df = apply(df, op)
	return df

# @debug
def category(df, c):
	return pd.concat([one(df, o) for o in c['concatenate']])

def from_df(df, config):
	df['timestamp'] = df['timestamp']-min(df['timestamp'])
	df = pd.DataFrame(df)
	concat = [
		category(df, config['c'][i]).assign(c=i)
		for i in range(len(config['c']))
	]
	for i in range(len(concat)):
		config['c'][i]['len'] = len(concat[i])
	df = pd.concat(concat)
	df['c'] = df['c'].astype(pd.CategoricalDtype(ordered=True))
	df = df[config['shape']]
	df = dask.dataframe.from_pandas(df, npartitions=cpu_count())
	df.persist() # Persist multiple Dask collections into memory
	return df
