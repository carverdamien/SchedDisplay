from threading import Thread, Semaphore
from multiprocessing import cpu_count
import time, itertools
import numpy as np

COMPUTABLE={}

def add(dependencies, name):
	def warp(function):
		def f(dd, log=print):
			for k in dependencies:
				log(f'{k} is a depency of {name}')
				if k not in dd:
					dd[k] = COMPUTABLE[k](dd, log=log)
			start = time.time()
			r = function(dd, log=log)
			end = time.time()
			log(f'Computing {name} took {end-start}s')
			return r
		f.__name__ = name
		assert f.__name__ not in COMPUTABLE
		COMPUTABLE[f.__name__] = f
		return f
	return warp

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

def extra(*extra_args, **extra_kwargs):
	def wrap(function):
		def f(*args, **kwargs):
			args = args + extra_args
			kwargs.update(extra_kwargs)
			return function(*args, **kwargs)
		return f
	return wrap

for key in ['timestamp', 'arg0', 'arg1']:
	@add([key,'event','cpu'], f'nxt_{key}_of_same_evt_on_same_cpu')
	@extra(key)
	def parallel_nxt_of_same_evt_on_same_cpu(dd, key, log=print):
		nxt = np.array(dd[key])
		idx = np.arange(len(nxt))
		events = np.unique(dd['event'])
		cpus = np.unique(dd['cpu'])
		# Compute == once only
		sel_evt = { evt : np.array(dd['event'] == evt) for evt in events}
		sel_cpu = { cpu :   np.array(dd['cpu'] == cpu) for cpu in cpus}
		iter_args = itertools.product(events, cpus)
		@parallel(iter_args)
		def compute_nxt(evt, cpu):
			sel = (sel_evt[evt]) & (sel_cpu[cpu])
			nxt[idx[sel][:-1]] = nxt[idx[sel][1:]]
		compute_nxt()
		return nxt
	@add([key,'event','pid'], f'nxt_{key}_of_same_evt_of_same_pid')
	@extra(key)
	def parallel_nxt_of_same_evt_of_same_pid(dd, key, log=print):
		nxt = np.array(dd[key])
		idx = np.arange(len(nxt))
		events = np.unique(dd['event'])
		pids = np.unique(dd['pid'])
		# Compute == once only
		sel_evt = { evt : np.array(dd['event'] == evt) for evt in events}
		sel_pid = { pid :   np.array(dd['pid'] == pid) for pid in pids}
		iter_args = itertools.product(events, pids)
		@parallel(iter_args)
		def compute_nxt(evt, pid):
			sel = (sel_evt[evt]) & (sel_pid[pid])
			nxt[idx[sel][:-1]] = nxt[idx[sel][1:]]
		compute_nxt()
		return nxt
