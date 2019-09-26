from smv.ViewController import ViewController
from bokeh.models.widgets import DataTable
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TableColumn
from bokeh.models.widgets import Button
from bokeh.layouts import column, row
import pandas as pd
from tornado import gen
from functools import partial
from threading import Lock, Thread
import traceback

class TableViewController(ViewController):
	"""docstring for TableViewController"""
	def __init__(self, **kwargs):
		self.model = kwargs['model']
		self.lock = Lock()
		self.source = kwargs.get('source', ColumnDataSource({}))
		self.table = DataTable(
			source=self.source,
			sizing_mode='stretch_both',
			width_policy='max',
			selectable=True,
		)
		self.load_button = Button(
			label='Load',
			align="end",
			button_type="success",
			width=100,
			width_policy="fixed",
			height=40,
			height_policy="fixed",
		)
		self.build_button = Button(
			label='Update',
			align="end",
			button_type="success",
			width=100,
			width_policy="fixed",
			height=40,
			height_policy="fixed",
		)
		self.stream_button = Button(
			label='Stream Update',
			align="end",
			button_type="success",
			width=100,
			width_policy="fixed",
			height=40,
			height_policy="fixed",
		)
		self.save_button = Button(
			label='Save',
			align="end",
			button_type="success",
			width=100,
			width_policy="fixed",
			height=40,
			height_policy="fixed",
		)
		self.stream_and_save_button = Button(
			label='Update',
			align="end",
			button_type="success",
			width=100,
			width_policy="fixed",
			height=40,
			height_policy="fixed",
		)
		view = column(
			row(
				self.load_button,
				self.build_button,
				self.stream_button,
				self.save_button,
				self.stream_and_save_button,
				sizing_mode='stretch_width'
			),
			self.table,
			sizing_mode='stretch_both',
		)
		super(TableViewController, self).__init__(view, **kwargs)
		self.build_button.on_click(self.build)
		self.stream_button.on_click(self.stream)
		self.load_button.on_click(self.load)
		self.save_button.on_click(self.save)
		self.stream_and_save_button.on_click(self.stream_and_save)


	##########################
	# Non-blocking Functions #
	##########################

	def stream_and_save(self, event):
		fname = self.stream_and_save.__name__
		if not self.lock.acquire(False):
			self.log('Could not acquire lock in {}'.format(fname))
			return
		def target():
			try:
				def callback(df):
					a = frozenset(k for k in self.source.data.keys() if k != 'index')
					b = frozenset(df.columns)
					if hash(a) == hash(b):
						self.stream_source(df)
					else:
						self.update_source(df)
				self.model.stream(callback)
				self.model.join()
				self.model.save()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
			else:
				self.lock.release()
		Thread(target=target).start()

	def build(self, event):
		fname = self.build.__name__
		if not self.lock.acquire(False):
			self.log('Could not acquire lock in {}'.format(fname))
			return
		def target():
			try:
				df = self.model.build()
				self.update_source(df)
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
			else:
				self.lock.release()
		Thread(target=target).start()

	def stream(self, event):
		fname = self.stream.__name__
		if not self.lock.acquire(False):
			self.log('Could not acquire lock in {}'.format(fname))
			return
		def target():
			try:
				def callback(df):
					a = frozenset(k for k in self.source.data.keys() if k != 'index')
					b = frozenset(df.columns)
					if hash(a) == hash(b):
						self.stream_source(df)
					else:
						self.update_source(df)
				self.model.stream(callback)
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
			else:
				self.lock.release()
		Thread(target=target).start()

	def load(self, event):
		fname = self.load.__name__
		if not self.lock.acquire(False):
			self.log('Could not acquire lock in {}'.format(fname))
			return
		def target():
			try:
				self.model.load()
				self.update_source(self.model.df)
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
			else:
				self.lock.release()
		Thread(target=target).start()

	def save(self, event):
		fname = self.save.__name__
		if not self.lock.acquire(False):
			self.log('Could not acquire lock in {}'.format(fname))
			return
		def target():
			try:
				self.model.save()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
			else:
				self.lock.release()
		Thread(target=target).start()

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

	def stream_source(self, df):
		@gen.coroutine
		def coroutine(df):
			self.source.stream(df)
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine, df))

	###############################
	# Compute intensive functions #
	###############################
