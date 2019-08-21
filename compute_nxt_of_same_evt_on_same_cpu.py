#!/usr/bin/env python3
import time
import sys
import smv.DataDict as DataDict
import numpy as np
from threading import Thread
from multiprocessing import cpu_count, Semaphore

def log(func):
	def f(*args, **kwargs):
		start = time.time()
		print('{}({}) starts at {}'.format(func.__name__, str(args), start))
		r = func(*args, **kwargs)
		end = time.time()
		print('{}({}) took {} s'.format(func.__name__, str(args), end - start))
		return r
	return f

@log
def nxt_of_same_evt_on_same_cpu(dd, key):
	nxt = np.array(dd[key])
	idx = np.arange(len(nxt))
	events = np.unique(dd['event'])
	cpus = np.unique(dd['cpu'])
	# Compute == once only
	sel_evt = { evt : np.array(dd['event'] == evt) for evt in events}
	sel_cpu = { cpu :   np.array(dd['cpu'] == cpu) for cpu in cpus}
	#
	# TODO: write a pragma parallel decorator
	#
	sem = Semaphore(cpu_count())
	def target(evt, cpu):
		sem.acquire()
		sel = (sel_evt[evt]) & (sel_cpu[cpu])
		nxt[idx[sel][:-1]] = nxt[idx[sel][1:]]
		sem.release()
	def spawn(evt, cpu):
		t = Thread(target=target, args=(evt,cpu))
		t.start()
		return t
	threads = [
		spawn(evt,cpu)
		for evt in events
		for cpu in cpus
	]
	for t in threads:
		t.join()
	return nxt

@log
def main():
	_, tar = sys.argv
	dd = DataDict.from_tar(tar)
	print(dd)
	dd['nxt_timestamp_of_same_evt_on_same_cpu'] = nxt_of_same_evt_on_same_cpu(dd, 'timestamp')
	print(dd)
	pass

if __name__ == '__main__':
	main()
