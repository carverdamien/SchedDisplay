from bokeh.plotting import curdoc
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TableColumn
from tornado import gen
from functools import partial
import json
import pandas as pd
import bg.loadDataFrame

class State(object):
	"""docstring for State"""
	def __init__(self, doc):
		super(State, self).__init__()
		self.doc = doc
		self.STATE = {
			'hdf5' : [],
		}
		self.DF = {}

	def from_json(self, new_state, done):
		new_state = json.loads(new_state)
		self.STATE['hdf5'].clear()
		self.DF.clear()
		self.load_many_hdf5(new_state['hdf5'], done)

	def to_json(self):
		return json.dumps(self.STATE)

	def is_valid(self, new_state):
		try:
			return not self.to_json() == json.dumps(json.loads(new_state))
		except json.decoder.JSONDecodeError as e:
			pass
		return False

	def hdf5_is_loaded(self, path):
		return path in self.STATE['hdf5']

	@gen.coroutine
	def coroutine_load_hdf5(self, path, df, done):
		self.DF[path] = df
		self.STATE['hdf5'].append(path)
		done()

	def callback_load_hdf5(self, path, df, done):
	    self.doc.add_next_tick_callback(partial(self.coroutine_load_hdf5, path, df, done))
	def load_hdf5(self, path, done):
		bg.loadDataFrame.bg(path, self.callback_load_hdf5, done).start()
	def load_many_hdf5(self, paths, done):
		if len(paths) == 0:
			done()
		else:
			def my_done():
				self.load_many_hdf5(paths[1:], done)
			self.load_hdf5(paths[0], my_done)
	def unload_hdf5(self, path):
		del self.DF[path]
		self.STATE['hdf5'].remove(path)
	def update_source(self, src):
		# src.data = ColumnDataSource.from_df(DF[0])
		pass
	def update_table(self, table):
		# table.columns = [TableColumn(field=c, title=c) for c in DF[0].columns]
		pass
