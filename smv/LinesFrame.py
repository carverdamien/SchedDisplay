#
# TODO: rename this file.
# It allows users to process the trace into something else
# A LinesFrame, A PointsFrame
#
import pandas as pd
#
# TODO: do not import pandas
# Try use numpy only to improve perf and memory.
# This would imply rewrite functions:
# * query into ==, <=, <, >=, >, |, &
# * assign into =
#
from multiprocessing import cpu_count
import numpy as np
import time
from smv.ConsoleViewController import logFunctionCall
from threading import Thread, Semaphore
import traceback

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
		s = s + a
	return s

# @debug
def sub(df, *args):
	args = list(args)
	INSTANCE=(int, float, np.ndarray, pd.Series)
	for i in range(len(args)):
		if not isinstance(args[i], INSTANCE):
			args[i] = apply(df, args[i])
		assert isinstance(args[i], INSTANCE), "{} is not good type".format(args[i])
	s = args[0]
	for a in args[1:]:
		s = s-a
	return s

def div(df, *args):
	args = list(args)
	INSTANCE=(int, float, np.ndarray, pd.Series)
	for i in range(len(args)):
		if not isinstance(args[i], INSTANCE):
			args[i] = apply(df, args[i])
		assert isinstance(args[i], INSTANCE), "{} is not good type".format(args[i])
	s = args[0]
	for a in args[1:]:
		s = s/a
	return s

def rolling(df, window, op, key):
	rolling_op = ['sum','mean','median'] # etc...
	assert isinstance(window, int), f"{window} must be int"
	assert op in rolling_op, f"{op} must be in {rolling_op}"
	return df[key].rolling(window).agg({key:op})[key]

OP = {
	'query':query,
	'=':assign,
	'+':add,
	'-':sub,
	'/':div,
	'rolling': rolling,
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
def one(df, i, operators, output, log=default_log):
	for op in operators:
		log('c[{}] Processing {}'.format(i, op))
		df = apply(df, op)
	return df.assign(c=i)[output].dropna(how='any')

# @debug
def category(df, i, config, log=default_log):
	output = config['output']
	c = config['c'][i]
	log('c[{}] Processing {}'.format(i, c))
	return pd.concat([one(df, i, o, output, log=log) for o in c['concatenate']])

def from_df(df, config, log=default_log):
	@logFunctionCall(log)
	def subtract_min_timestamp(df):
		# return df['timestamp']-min(df['timestamp'])
		# assert min(df['timestamp']) == df['timestamp'][0]
		t0 = df['timestamp'][0]
		df['timestamp'] -= t0
		if 'nxt_timestamp_of_same_evt_on_same_cpu' in df:
			df['nxt_timestamp_of_same_evt_on_same_cpu'] -= t0
	subtract_min_timestamp(df)
	@logFunctionCall(log)
	def array_to_dataframe(df):
		return pd.DataFrame(df)
	df = array_to_dataframe(df)
	# Sequential
	# @logFunctionCall(log)
	# def compute_categories(df, config):
	# 	return [
	# 		category(df, i, config, log=log)
	# 		for i in range(len(config['c']))
	# 	]
	# Parallel
	#
	# TODO: write a pragma parallel decorator
	#
	@logFunctionCall(log)
	def compute_categories(df, config):
		sem = Semaphore(cpu_count())
		result = [None]*len(config['c'])
		def target(df, i, config, log):
			sem.acquire()
			try:
				result[i] = category(df, i, config, log=log)
			except Exception as e:
				log(traceback.format_exc())
			sem.release()
		def spawn(*args):
			t = Thread(target=target,args=args)
			t.start()
			return t
		threads = [
			spawn(df, i, config, log)
			for i in range(len(config['c']))
		]
		for t in threads:
			t.join()
		return result
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
	return df
