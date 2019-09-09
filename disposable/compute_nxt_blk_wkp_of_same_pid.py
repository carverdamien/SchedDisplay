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

def parallel_compute(dd):
	# TODO
	return sequential_compute(dd)

def sequential_compute(dd):
	# TODO
	nxt = np.array(dd['timestamp'])
	idx = np.arange(len(nxt))
	pid = np.unique(dd['pid'])
	sel_evt = (dd['event'] == BLOCK) | (dd['event']==WAKEUP)
	def per_pid(p):
		sel_pid = dd['pid'] == p
		sel = sel_evt & sel_pid
		nxt[idx[sel][:-1]] = nxt[idx[sel][1:]]
	for p in pid:
		per_pid(p)
	return nxt

def dummy_data():
	event = [
		ENQ,
		EXEC,
		ENQ,
		BLOCK,
		ENQ,
		WAKEUP,
		ENQ,
		BLOCK,
		# Should we detect this?
		BLOCK,
		WAKEUP,
		WAKEUP,
		EXIT,
	]
	N = len(event)
	return {
		'timestamp' : np.arange(2*N),
		'pid'       : np.array([0]*N+[1]*N),
		'event'     : np.array(event+event)
	}

@log
def main():
	NAME = 'nxt_of_same_pid'
	# _, tar = sys.argv
	# dd = DataDict.from_tar(tar)
	dd = dummy_data()
	dd = {k:dd[k] for k in dd if k in ['timestamp','pid','event']}
	dd[NAME] = parallel_compute(dd)
	import pandas as pd
	print(pd.DataFrame(dd))
	# DataDict.add_array_to_tar(tar,NAME,dd[NAME])
	pass

if __name__ == '__main__':
	main()
