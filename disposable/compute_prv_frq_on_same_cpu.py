#!/usr/bin/env python3
import time
import sys
import smv.DataDict as DataDict
import numpy as np
from threading import Thread
from multiprocessing import cpu_count, Semaphore
import itertools

EXEC=0
EXIT=1
WAKEUP=2
BLOCK=4
TICK=10
ENQ=13

def log(func):
	def f(*args, **kwargs):
		start = time.time()
		#print('{}({}) starts at {}'.format(func.__name__, str(args), start))
		r = func(*args, **kwargs)
		end = time.time()
		#print('{}({}) took {} s'.format(func.__name__, str(args), end - start))
		print('{} took {} s'.format(func.__name__, end - start))
		return r
	return f

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

@log
def parallel_compute(dd):
	# return sequential_compute(dd)
	sel_evt = dd['event'] == TICK
	N = len(dd['arg1'])
	nxt = np.empty(N)
	nxt[:] = np.NaN
	nxt[sel_evt] = dd['arg1'][sel_evt]
	idx = np.arange(N)
	cpu = np.unique(dd['cpu'])
	@parallel(itertools.product(cpu))
	def per_cpu(c):
		sel = dd['cpu'] == c
		nan = np.isnan(nxt[sel])
		inxt = np.where(~nan, idx[sel], 0)
		np.maximum.accumulate(inxt, out=inxt)
		nxt[sel] = nxt[inxt]
	per_cpu()
	return nxt

@log
def sequential_compute(dd):
	sel_evt = dd['event'] == TICK
	N = len(dd['arg1'])
	nxt = np.empty(N)
	nxt[:] = np.NaN
	nxt[sel_evt] = dd['arg1'][sel_evt]
	idx = np.arange(N)
	cpu = np.unique(dd['cpu'])
	def per_cpu(c):
		sel = dd['cpu'] == c
		nan = np.isnan(nxt[sel])
		inxt = np.where(~nan, idx[sel], 0)
		np.maximum.accumulate(inxt, out=inxt)
		nxt[sel] = nxt[inxt]
	for c in cpu:
		per_cpu(c)
	return nxt

def dummy_data():
	event = [
		EXEC,
		TICK,
		BLOCK,
		WAKEUP,
		TICK,
		EXIT,
	]
	N = len(event)
	arg1 = [np.NaN if event[i] != TICK else i for i in range(N)]
	# return {
	# 	'cpu'       : np.array([0]*N),
	# 	'event'     : np.array(event),
	# 	'arg1'      : np.array(arg1)
	# }
	return {
		'cpu'       : np.array([0]*N+[1]*N),
		'event'     : np.array(event+event),
		'arg1'      : np.array(arg1+arg1)
	}

@log
def main():
	NAME = 'prv_frq_on_same_cpu'
	_, tar = sys.argv
	# tar = 'examples/trace/32-patchlocal.tar'
	dd = DataDict.from_tar(tar, only=['event','cpu', 'arg1'])
	# dd = dummy_data()
	# assert np.sum(np.diff(dd['timestamp'])<0) == 0
	# dd = dummy_data()
	dd[NAME] = parallel_compute(dd)
	# assert np.array_equal(dd[NAME], sequential_compute(dd))
	#dd['diff'] = dd[NAME] - dd['timestamp']
	#import pandas as pd
	#pddd = pd.DataFrame(dd)
	#print(pddd)
	#print(pddd[pddd['diff']>0])
	DataDict.add_array_to_tar(tar,NAME,dd[NAME])
	pass

if __name__ == '__main__':
	main()
