from threading import Thread
from multiprocessing import cpu_count, Semaphore

COMPUTABLE={}

def add(dependencies, name):
	def warp(function):
		def f(dd):
			for k in dependencies:
				if k not in dd:
					dd[k] = COMPUTABLE[k](dd)
			return function(dd)
		f.__name__ = name
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

for key in ['timestamp', 'arg0', 'arg1']:
	@add([],name=f'nxt_{key}_of_same_evt_on_same_cpu')
	def parallel_nxt_of_same_evt_on_same_cpu(dd):
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
	@add([],name=f'nxt_{key}_of_same_evt_with_same_pid')
	def parallel_nxt_of_same_evt_on_same_cpu(dd):
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

print(COMPUTABLE)
