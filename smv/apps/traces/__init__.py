from bokeh.models.widgets import DataTable
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TableColumn
import tarfile, os
import pandas as pd
from tornado import gen
from functools import partial
from threading import Lock, Thread
import numpy as np
import parse

__NP_COLUMNS__ = []
__COLUMNS__ = []

def column(is_np_column=True):
	def decorator(function):
		def f(*args, **kwargs):
			return function(*args, **kwargs)
		f.__name__ = function.__name__
		__COLUMNS__.append(f)
		if is_np_column:
			__NP_COLUMNS__.append(f)
		return f
	return decorator

def parsable_column(basename, pattern, is_np_column=True):
	def decorator(function):
		def f(*args, **kwargs):
			index = args[0]
			with tarfile.open(index, 'r') as tar:
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
			return function(*args, **kwargs)
		f.__name__ = function.__name__
		__COLUMNS__.append(f)
		if is_np_column:
			__NP_COLUMNS__.append(f)
		return f
	return decorator

@column(is_np_column=False)
def fname(*args, **kwargs):
	index = args[0]
	# import time
	# time.sleep(1) # simulate slow work
	return index

def modify_doc(doc):
	source = ColumnDataSource({
		c.__name__ : (np.array([]) if c in __NP_COLUMNS__ else [])
		for c in __COLUMNS__
	})
	table = DataTable(
		source=source,
		columns=[TableColumn(field=c.__name__, title=c.__name__) for c in __COLUMNS__],
		sizing_mode='stretch_both',
		width_policy='max',
		selectable=True,
	)
	@gen.coroutine
	def coroutine(row):
		source.stream(row)
	def target():
		try:
			for index in sorted(list(find_files('examples/trace','.tar'))):
				# row = {c.__name__:np.array([c(index)]) for c in __COLUMNS__}
				row = {
					c.__name__: (np.array([c(index)]) if c in __NP_COLUMNS__ else [c(index)])
					for c in __COLUMNS__
				}
				doc.add_next_tick_callback(partial(coroutine, row))
		except Exception as e:
			print(e)
			raise e
	Thread(target=target).start()
	# target() # debug
	doc.add_root(table)
	pass

def find_files(directory, ext):
	for root, dirs, files in os.walk(directory, topdown=False):
		for name in files:
			path = os.path.join(root, name)
			if ext == os.path.splitext(name)[1]:
				yield path

@parsable_column('time.err','{pattern:F}')
def usr_bin_time(index):
	return np.NaN

@parsable_column('run.out','{:s}transactions:{:s}{:d}{:s}({pattern:F} per sec.)')
def sysbench_trps(index):
	return np.NaN

@parsable_column('cpu-energy-meter.out','cpu0_package_joules={pattern:F}')
def cpu0_package_joules(index):
	return np.NaN

@parsable_column('cpu-energy-meter.out','cpu1_package_joules={pattern:F}')
def cpu1_package_joules(index):
	return np.NaN

@parsable_column('cpu-energy-meter.out','cpu2_package_joules={pattern:F}')
def cpu2_package_joules(index):
	return np.NaN

@parsable_column('cpu-energy-meter.out','cpu3_package_joules={pattern:F}')
def cpu3_package_joules(index):
	return np.NaN

@parsable_column('cpu-energy-meter.out','cpu0_dram_joules={pattern:F}')
def cpu0_dram_joules(index):
	return np.NaN

@parsable_column('cpu-energy-meter.out','cpu1_dram_joules={pattern:F}')
def cpu1_dram_joules(index):
	return np.NaN

@parsable_column('cpu-energy-meter.out','cpu2_dram_joules={pattern:F}')
def cpu2_dram_joules(index):
	return np.NaN

@parsable_column('cpu-energy-meter.out','cpu3_dram_joules={pattern:F}')
def cpu3_dram_joules(index):
	return np.NaN
