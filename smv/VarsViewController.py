from smv.ViewController import ViewController
from bokeh.models.widgets import DataTable
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TableColumn
from bokeh.models.widgets import Div
from bokeh.layouts import column, row
import pandas as pd
from tornado import gen
from functools import partial
from threading import Lock, Thread
import traceback
import string

DEFAULT_VARS = {
	'EXEC'    : '0',
	'EXIT'    : '1',
	'WAKEUP'      : '2',
	'WAKEUP_NEW'  : '3',
	'BLOCK'       : '4',
	'BLOCK_IO'    : '5',
	'WAIT_FUTEX'  : '6',
	'WAKE_FUTEX' : '7',
	'WAKER_FUTEX'  : '8',
	'FORK'    : '9',
	'TICK'    : '10',
	'CTX_SWITCH'  : '11',
	'MIGRATE' : '12',
	'RQ_SIZE'     : '13',
	'IDL_BLN_FAIR_BEG' : '14',
	'IDL_BLN_FAIR_END' : '15',
	'PERIODIC_BALANCE_BEG' : '16',
	'PERIODIC_BALANCE_END' : '17',
}

class VarsViewController(ViewController):
	"""docstring for VarsViewController"""
	def __init__(self, **kwargs):
		# Provide source. (Do not use defaut)
		self.title = ''
		self.lock = Lock()
		self.vars = kwargs.get('vars', DEFAULT_VARS)
		self.source = kwargs.get('source', ColumnDataSource({}))
		self.table = DataTable(
			source=self.source,
			sizing_mode='stretch_both',
			width_policy='max',
			selectable=True,
		)
		self.div = Div(
			visible=True,
			width_policy='max',
			height_policy='min',
		)
		view = column(
			self.div,
			self.table,
			sizing_mode='stretch_both',
		)
		super(VarsViewController, self).__init__(view, **kwargs)
		self.update_source(self.compute_df(self.vars))
		self.update_div()


	##########################
	# Non-blocking Functions #
	##########################

	def parse(self, o):
		if isinstance(o, dict):
			for k in o:
				o[k] = self.parse(o[k])
		elif isinstance(o, list):
			for i in range(len(o)):
				o[i] = self.parse(o[i])
		elif isinstance(o, str):
			t = string.Template(o)
			o = t.substitute(**self.vars)
		else:
			pass
		return o

	def update_vars(self, **kwargs):
		fname = self.update_vars.__name__
		if not self.lock.acquire(False):
			self.log('Could not acquire ock lin {}'.format(fname))
			return
		def target(**kwargs):
			try:
				self.vars.update(kwargs)
				df = self.compute_df(self.vars)
				self.update_source(df)
				self.update_div()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
			else:
				self.lock.release()
		Thread(target=target, kwargs=kwargs).start()

	####################################
	# Functions modifying the document #
	####################################

	def update_source(self, df):
		@gen.coroutine
		def coroutine(df):
			self.table.columns = [TableColumn(field=c, title=c) for c in df.columns]
			self.source.data = ColumnDataSource.from_df(df)
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine, df))

	def update_div(self):
		@gen.coroutine
		def coroutine():
			self.div.text = f"{self.title}"
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine))

	###############################
	# Compute intensive functions #
	###############################

	def compute_df(self, vars):
		keys = list(vars.keys())
		values = [vars[k] for k in keys]
		keys = [f"${k}" for k in keys]
		return pd.DataFrame({"key":keys, "value":values})
