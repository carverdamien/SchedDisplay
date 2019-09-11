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

class StatsViewController(ViewController):
	"""docstring for StatsViewController"""
	def __init__(self, **kwargs):
		# Provide source. (Do not use defaut)
		self.title = ''
		self.info = ''
		self.lock = Lock()
		self.source = kwargs.get('source', ColumnDataSource({}))
		self.table = DataTable(
			source=self.source,
			sizing_mode='stretch_both',
			width_policy='max',
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
		super(StatsViewController, self).__init__(view, **kwargs)


	##########################
	# Non-blocking Functions #
	##########################

	def update_stats(self, **kwargs):
		fname = self.update_stats.__name__
		if not self.lock.acquire(False):
			self.log('Could not acquire ock in {}'.format(fname))
			return
		def target(**kwargs):
			try:
				data = kwargs['data']
				self.info = kwargs.get('query', self.info)
				df = self.compute_stats(data)
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
			self.div.text = f"{self.title} {self.info}"
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine))

	###############################
	# Compute intensive functions #
	###############################

	def compute_stats(self, data):
		df = data.groupby('c').agg(['mean','sum','count']).compute()
		df = pd.DataFrame({"{}.{}".format(i,j):df[i][j] for i,j in df.columns})
		return df
