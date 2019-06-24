from bokeh.plotting import curdoc
from bokeh.models import ColumnDataSource, IndexFilter
from bokeh.models.widgets import TableColumn
from bokeh.models.glyphs import Segment
from bokeh.models import Legend, LegendItem
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
			'columns' : {
				'x0':['copy','timestamp'],
				'x1':['copy', 'timestamp'],
				'y0':['copy', 'cpu'],
				'y1':['+',['copy', 'cpu'],0.75],
			},
			'renderers' : [
				{
					'label':'all_events',
					'filter' : [],
					'x0':'x0',
					'x1':'x1',
					'y0':'y0',
					'y1':'y1',
					'line_color' : '#0000FF',
				},
				{
					'label':'event0',
					'filter' : ['==','event',0],
					'x0':'x0',
					'x1':'x1',
					'y0':'y0',
					'y1':'y1',
					'line_color' : '#FF0000',
				},
				{
					'label':'all event13 of pid0',
					'filter' : ['&',['==','pid',0],['==','event',13]],
					'x0':'x0',
					'x1':'x1',
					'y0':'y0',
					'y1':'y1',
					'line_color' : '#00FF00',
				},
				{
					'label':'all events of make',
					'filter' : ['==','comm','make'],
					'x0':'x0',
					'x1':'x1',
					'y0':'y0',
					'y1':'y1',
					'line_color' : '#000000',
				},
			],
		}
		self.DF = pd.DataFrame()
		self.path_id = {}
		self.path_id_next = 0

	def from_json(self, new_state, done):
		new_state = json.loads(new_state)
		self.STATE['renderers'].clear()
		self.STATE['renderers'] = new_state['renderers']
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
		self.compute_columns()
		self.STATE['hdf5'].append(path)
		self.update_source()
		self.update_view()
		self.update_table()
		self.update_plot()
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
		self.compute_columns()
		self.STATE['hdf5'].remove(path)
		self.update_source()
		self.update_view()
		self.update_table()
		self.update_plot()
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
	def compute_columns(self):
		# TODO: read and exec STATE['columns']
		self.DF['x0'] = self.DF['timestamp']
		self.DF['x1'] = self.DF['x0']
		self.DF['y0'] = self.DF['cpu']
		self.DF['y1'] = self.DF['y0'] + .75
		pass
	def update_plot(self):
		self.plot.renderers.clear()
		items = []
		index = 0
		for r in self.STATE['renderers']:
			glyph = Segment(
				x0=r['x0'],
				x1=r['x1'],
				y0=r['y0'],
				y1=r['y1'],
				line_color=r['line_color'],
			)
			_r = self.plot.add_glyph(self.source, glyph, view=self.view)
			items.append(LegendItem(label=r['label'], renderers=[_r], index=index))
			index+=1
		self.plot.legend.items = items
		pass
