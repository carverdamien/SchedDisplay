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

__COLUMNS__ = []
def column(function):
	def f(*args, **kwargs):
		return function(*args, **kwargs)
	f.__name__ = function.__name__
	__COLUMNS__.append(f)
	return f

@column
def fname(index):
	# import time
	# time.sleep(1) # simulate slow work
	return index

def modify_doc(doc):
	source = ColumnDataSource({c.__name__:np.array([]) for c in __COLUMNS__})
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
				row = {c.__name__:np.array([c(index)]) for c in __COLUMNS__}
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

@column
def time(index):
	with tarfile.open(index, 'r') as tar:
		for tarinfo in tar:
			if os.path.basename(tarinfo.name) != 'time.err':
				continue
			with tar.extractfile(tarinfo.name) as f:
				re = parse.compile("{time:F}")
				for line in f.read().decode().split('\n'):
					r = re.parse(line)
					if r is not None:
						return r.named['time']
			break
	return np.NaN
