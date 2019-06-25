import logging
from bokeh.plotting import curdoc
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TableColumn
from bokeh.models.glyphs import Segment
from bokeh.models import Legend, LegendItem
from tornado import gen
from functools import partial
import json
import pandas as pd
import numpy as np
import sched_monitor_view.bg.loadDataFrame
import sched_monitor_view.lang.filter
import sched_monitor_view.lang.columns

class State(object):
	"""docstring for State"""
	def __init__(self, doc, table, plot):
		super(State, self).__init__()
		self.doc = doc
		self.table = table
		self.plot = plot
		self.STATE = {
			'hdf5' : [],
			'truncate' : {'mode':'index', 'cursor': 0, 'width': 1},
			'columns' : {'y1':['+',['copy', 'cpu'],0.75],},
			'renderers' : [
			],
		}
		self.DF = pd.DataFrame()
		self.comm = {}
		self.path_id = {}
		self.path_id_next = 0
		self.source = []

	def from_json(self, new_state, done):
		new_state = json.loads(new_state)
		self.plot.renderers.clear()
		self.source.clear()
		self.STATE['renderers'].clear()
		self.STATE['renderers'] = new_state['renderers']
		self.STATE['hdf5'].clear()
		self.DF = pd.DataFrame()
		self.load_many_hdf5(new_state['hdf5'], done)
		self.STATE['truncate'] = new_state['truncate']
		self.truncate(**new_state['truncate'])

	def to_json(self):
		return json.dumps(self.STATE)

	def to_pretty_json(self):
		return json.dumps(self.STATE, indent=4, sort_keys=True)

	def is_valid(self, new_state):
		try:
			return not self.to_json() == json.dumps(json.loads(new_state))
		except json.decoder.JSONDecodeError as e:
			pass
		return False

	def hdf5_is_loaded(self, path):
		return path in self.STATE['hdf5']

	@gen.coroutine
	def coroutine_load_hdf5(self, path, data, done):
		logging.debug('coroutine_load_hdf5 starts')
		df = data['df']
		self.comm.clear()
		self.comm.update(data['comm'])
		self.DF = self.DF.append(df, ignore_index=True)
		self.DF.sort_values(by='timestamp', inplace=True)
		self.DF.index = np.arange(len(self.DF))
		self.compute_columns()
		self.STATE['hdf5'].append(path)
		self.update_plot()
		self.update_source()
		self.update_table()
		done()
		logging.debug('coroutine_load_hdf5 ends')

	def callback_load_hdf5(self, path, data, done):
	    self.doc.add_next_tick_callback(partial(self.coroutine_load_hdf5, path, data, done))
	def load_hdf5(self, path, done):
		if path not in self.path_id:
			self.path_id[path] = self.path_id_next
			self.path_id_next += 1
		path_id = self.path_id[path]
		sched_monitor_view.bg.loadDataFrame.bg(path, path_id, self.callback_load_hdf5, done).start()
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
		self.compute_columns()
		self.STATE['hdf5'].remove(path)
		self.update_plot()
		self.update_source()
		self.update_table()
	def update_source(self):
		logging.debug('update_source starts')
		sellim = self.sellim()
		for s,f in self.source:
			sel = sellim & sched_monitor_view.lang.filter.sel(self.DF, f)
			df = self.DF[sel]
			s.data = ColumnDataSource.from_df(df)
		logging.debug('update_source ends')
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
		self.update_source()
		self.update_table()
		return cursor, width
	def sellim(self):
		sellim = np.zeros(len(self.DF), dtype=bool)
		cursor = self.STATE['truncate']['cursor']
		width  = self.STATE['truncate']['width']
		if self.STATE['truncate']['mode'] == 'index':
			end = min(len(sellim), cursor+width)
			sellim[cursor:cursor+width] = True
		elif self.STATE['truncate']['mode'] == 'time':
			# TODO: use np.searchsorted
			sellim = (self.DF['timestamp'] >= cursor) & (self.DF['timestamp'] <= (cursor+width))
		return sellim
	def update_table(self):
		logging.debug('update_table starts')
		if len(self.source) == 0:
			return
		sellim = self.sellim()
		s,f = self.source[0]
		sel = sellim & sched_monitor_view.lang.filter.sel(self.DF, f)
		df = self.DF[sel]
		self.table.source.data = ColumnDataSource.from_df(df)
		self.table.columns = [TableColumn(field=c, title=c) for c in df.columns]
		logging.debug('update_table ends')
		pass
	def compute_columns(self):
		for column in self.STATE['columns']:
			self.DF[column] = sched_monitor_view.lang.columns.compute(
				self.DF,
				self.STATE['columns'][column],
			)
	def update_plot(self):
		logging.debug('update_plot starts')
		self.plot.renderers.clear()
		self.source.clear()
		items = []
		index = 0
		for r in self.STATE['renderers']:
			source = ColumnDataSource({r[k]:[] for k in ['x0', 'x1', 'y0', 'y1']})
			glyph = Segment(
				x0=r['x0'],
				x1=r['x1'],
				y0=r['y0'],
				y1=r['y1'],
				line_color=r['line_color'],
			)
			_r = self.plot.add_glyph(source, glyph)
			items.append(LegendItem(label=r['label'], renderers=[_r], index=index))
			self.source.append((source, r['filter']))
			index+=1
		self.plot.legend.items = items
		logging.debug('update_plot ends')
		pass
