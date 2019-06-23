from bokeh.plotting import curdoc
from bokeh.models import ColumnDataSource, IndexFilter
from bokeh.models.widgets import TableColumn
from tornado import gen
from functools import partial
import json
import pandas as pd
import numpy as np
import bg.loadDataFrame

class State(object):
	"""docstring for State"""
	def __init__(self, doc, source, view, table, plot):
		super(State, self).__init__()
		self.doc = doc
		self.source = source
		self.view = view
		self.table = table
		self.plot = plot
		self.STATE = {
			'hdf5' : [],
			'truncate' : {'mode':'index', 'cursor': 0, 'width': 1},
		}
		self.DF = pd.DataFrame()
		self.path_id = {}
		self.path_id_next = 0

	def from_json(self, new_state, done):
		new_state = json.loads(new_state)
		self.STATE['hdf5'].clear()
		self.DF = pd.DataFrame()
		self.load_many_hdf5(new_state['hdf5'], done)
		self.STATE['truncate'] = new_state['truncate']
		self.truncate(**new_state['truncate'])

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
		self.DF = self.DF.append(df, ignore_index=True)
		self.DF.sort_values(by='timestamp', inplace=True)
		self.DF.index = np.arange(len(self.DF))
		self.STATE['hdf5'].append(path)
		self.update_source()
		self.update_view()
		self.update_table()
		done()

	def callback_load_hdf5(self, path, df, done):
	    self.doc.add_next_tick_callback(partial(self.coroutine_load_hdf5, path, df, done))
	def load_hdf5(self, path, done):
		if path not in self.path_id:
			self.path_id[path] = self.path_id_next
			self.path_id_next += 1
		path_id = self.path_id[path]
		bg.loadDataFrame.bg(path, path_id, self.callback_load_hdf5, done).start()
	def load_many_hdf5(self, paths, done):
		if len(paths) == 0:
			done()
		else:
			def my_done():
				self.load_many_hdf5(paths[1:], done)
			self.load_hdf5(paths[0], my_done)
	def unload_hdf5(self, path):
		path_id = self.path_id[path]
		sel = self.DF['path_id'] != path_id
		df = pd.DataFrame()
		if np.sum(sel) > 0:
			df = self.DF[sel]
		self.DF = pd.DataFrame().append(df, ignore_index=True)
		self.DF.sort_values(by='timestamp', inplace=True)
		self.DF.index = np.arange(len(self.DF))
		self.STATE['hdf5'].remove(path)
		self.update_source()
		self.update_view()
		self.update_table()
	def update_source(self):
		self.source.data = ColumnDataSource.from_df(self.DF)
		pass
	def get_truncate(self):
		mode = self.STATE['truncate']['mode']
		cursor = self.STATE['truncate']['cursor']
		width = self.STATE['truncate']['width']
		if mode == 'index':
			end = len(self.DF)
		elif mode == 'time':
			end = self.DF['timestamp'].iloc[-1]
		else:
			raise Exception('Unknown truncate mode')
		return mode, cursor, width, end
	def truncate(self, mode, cursor, width):
		if mode != self.STATE['truncate']['mode']:
			# TODO: dont reset, try to stay at the same place
			cursor = 0
			width = 1
		self.STATE['truncate'] = {'mode':mode, 'cursor': cursor, 'width':width}
		self.update_view()
		self.update_table()
		return cursor, width
	def update_view(self):
		index = self.DF.index
		if len(index) == 0:
			return
		cursor = self.STATE['truncate']['cursor']
		width  = self.STATE['truncate']['width']
		if self.STATE['truncate']['mode'] == 'index':
			indexfilter = IndexFilter(index[cursor:cursor+width])
		elif self.STATE['truncate']['mode'] == 'time':
			sel = (self.DF['timestamp'] >= cursor) & (self.DF['timestamp'] <= (cursor+width))
			indexfilter = IndexFilter(index[sel])
		else:
			raise Exception('Unknown truncate mode')
		self.view.filters = [indexfilter]
	def update_table(self):
		self.table.columns = [TableColumn(field=c, title=c) for c in self.DF.columns]
		pass
