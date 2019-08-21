#!/usr/bin/env python3
import time
import sys
import smv.DataDict as DataDict
import numpy as np
from threading import Thread
from multiprocessing import cpu_count, Semaphore
import numba

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
@numba.njit(parallel=True)
def numba_nxt_of_same_evt_on_same_cpu(dd_key, dd_event, dd_cpu):
	n = dd_key.shape[0]
	nxt = np.zeros(n)
	nxt[:]=dd_key
	idx = np.arange(len(nxt))
	events = np.sort(np.unique(dd_event))
	cpus = np.sort(np.unique(dd_cpu))
	# Compute == once only
	sel_evt = [dd_event == events[i] for i in range(len(events))]
	sel_cpu = [dd_cpu   == cpus[i]   for i in range(len(cpus))]
	for i in numba.prange(len(events)):
		for j in numba.prange(len(cpus)):
			sel = sel_evt[i] & sel_cpu[j]
			nxt[idx[sel][:-1]] = nxt[idx[sel][1:]]
	return nxt

@log
def main():
	_, tar = sys.argv
	dd = DataDict.from_tar(tar)
	dd = {k:dd[k] for k in dd if k in ['timestamp','cpu','event']}
	dd['nxt_timestamp_of_same_evt_on_same_cpu'] = nxt_of_same_evt_on_same_cpu(dd, 'timestamp')
	def try_numba():
		dd_key = dd['timestamp']
		dd_event = dd['event']
		dd_cpu = dd['cpu']
		# print(dd)
		dd['numba_nxt_timestamp_of_same_evt_on_same_cpu'] = numba_nxt_of_same_evt_on_same_cpu(
			dd_key,
			dd_event,
			dd_cpu,
		)
		dd['numba_nxt_timestamp_of_same_evt_on_same_cpu'] = numba_nxt_of_same_evt_on_same_cpu(
			dd_key,
			dd_event,
			dd_cpu,
		)
		print(np.sum(
			dd['nxt_timestamp_of_same_evt_on_same_cpu'] -
			dd['numba_nxt_timestamp_of_same_evt_on_same_cpu']
		))
	# I dont know why numba is twice slower
	# try_numba()
	# print(dd)
	pass

if __name__ == '__main__':
	main()
