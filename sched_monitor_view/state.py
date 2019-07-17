import datashader as ds
import datashader.transfer_functions as tf
from datashader.bokeh_ext import InteractiveImage
from bokeh.events import LODEnd

import logging
from bokeh.plotting import curdoc
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TableColumn
from bokeh.models.glyphs import Segment
from bokeh.models.tools import HoverTool
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
			'columns' : {},
			'renderers' : [
			],
		}
		self.DF = pd.DataFrame()
		# Add dummy point because datashader cannot handle emptyframe
		self.dfimg = pd.DataFrame({
			'x0':[0],
			'x1':[0],
			'y0':[0],
			'y1':[0],
			'category':[0],
		})
		self.dfimg['category'] = self.dfimg['category'].astype('category')
		self.comm = {}
		self.perf_event = {}
		self.path_id = {}
		self.path_id_next = 0
		self.source = []
		self.last_ranges = {}
		self.plot.on_event(LODEnd, self.callback_LODEnd)          # Has to be executed before inserting plot in doc
		self.img = InteractiveImage(self.plot, self.img_callback) # Has to be executed before inserting plot in doc
		assert(len(self.plot.renderers) == 1)
		self.datashader = self.plot.renderers[0]

	def from_json(self, new_state, done):
		new_state = json.loads(new_state)
		self.STATE['columns'] = new_state['columns']
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
		self.perf_event.clear()
		self.perf_event.update(data['perf_event'])
		self.DF = self.DF.append(df, ignore_index=True)
		self.DF.sort_values(by='timestamp', inplace=True)
		self.DF.index = np.arange(len(self.DF))
		self.compute_columns()
		self.compute_dimg()
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
		elif mode in ['time','datashader']:
			end = self.DF['timestamp'].iloc[-1]
		else:
			raise Exception('Unknown truncate mode')
		return mode, cursor, width, end
	def truncate(self, mode, cursor, width):
		update_plot = False
		if mode != self.STATE['truncate']['mode']:
			# TODO: dont reset, try to stay at the same place
			cursor = 0
			width = 1
			update_plot = 'datashader' in [mode, self.STATE['truncate']['mode']]
		self.STATE['truncate'] = {'mode':mode, 'cursor': cursor, 'width':width}
		self.update_source()
		self.update_table()
		if update_plot:
			self.update_plot()
		self.update_datashader()
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

	def compute_dimg(self):
		# Random df
		# tmax = 1000000000
		# N = 10000000
		# nr_cpu = 160
		# df = pd.DataFrame({
		# 	'timestamp':np.random.randint(0,tmax,N).astype(float),
		# 	'cpu':np.random.randint(0,nr_cpu,N).astype(float),
		# 	'event':np.random.randint(0,10,N),
		# 	'arg0':np.random.randint(0,2,N),
		# })
		# df.sort_values(by='timestamp', inplace=True)
		# df.index = np.arange(len(df))
		df = self.DF
		tmax = df['timestamp'].iloc[-1]
		nr_cpu = len(np.unique(df['cpu']))
		ymin = -1
		ymax = nr_cpu+1
		px_height = 4
		img_height = (nr_cpu+2)*px_height
		y0_shift = 0. / float(px_height)
		y1_shift = 2. / float(px_height)
		dfevt = pd.DataFrame({
			'x0':df['timestamp'],
			'x1':df['timestamp'],
			'y0':df['cpu']+y0_shift,
			'y1':df['cpu']+y1_shift,
			'category':df['event'],
		})
		# TODO intervals
		# dfint = pd.DataFrame({
		# 	'x0':df['timestamp'],
		# 	'x1':sched_monitor_view.lang.columns.compute(df, ['nxt_of_same_evt_on_same_cpu','timestamp']),
		# 	'y0':df['cpu'],
		# 	'y1':df['cpu'],
		# 	'category':df['event'],
		# })
		self.dfimg = dfevt # TODO intervals
		# dfimg = pd.concat([dfevt, dfint[sel]],ignore_index=True)
		self.dfimg['category'] = self.dfimg['category'].astype('category')
		# del dfevt
		# del dfint
		self.plot.x_range.start = 0
		self.plot.x_range.end = tmax
		self.plot.y_range.start = ymin
		self.plot.y_range.end = ymax
		self.plot.plot_width = 500
		self.plot.plot_height = img_height

	def img_callback(self, x_range, y_range, w, h, name=None):
		logging.debug('img_callback starts')
		cvs = ds.Canvas(plot_width=w, plot_height=h, x_range=x_range, y_range=y_range)
		agg = cvs.line(self.dfimg, x=['x0','x1'], y=['y0','y1'], agg=ds.count_cat('category'), axis=1)
		img = tf.shade(agg,min_alpha=255)
		logging.debug('img_callback ends')
		return img

	def callback_LODEnd(self, event):
		self.update_datashader()

	def update_datashader(self):
		if self.STATE['truncate']['mode'] != 'datashader':
			return
		try:
			nr_cpu = 160
			ymin = -1
			ymax = nr_cpu+1
			px_height = 4
			img_height = (nr_cpu+2)*px_height
			figure_plot = self.plot
			ranges = {
				'xmin':figure_plot.x_range.start,
				'xmax':figure_plot.x_range.end,
				'ymin':ymin, # do not use figure_plot.y_range.start
				'ymax':ymax, # do not use figure_plot.y_range.end
				'w':figure_plot.plot_width,
				'h':img_height, # do not use figure_plot.plot_height
			}
			last_ranges = self.last_ranges
			if hash(frozenset(last_ranges.items())) != hash(frozenset(ranges.items())):
				logging.debug('update_datashader starts')
				self.img.update_image(ranges)
				self.last_ranges = ranges
				logging.debug('update_datashader ends')
		except Exception as e:
			logging.debug('Exception({}):{}'.format(type(e),e))

	def update_plot(self):
		logging.debug('update_plot starts')
		self.plot.renderers.clear()
		if self.STATE['truncate']['mode'] == 'datashader':
			self.plot.renderers.append(self.datashader)
			return
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
		# TODO: add this in STATE
		TOOLTIPS = [
			("index","$index"),
			("timestamp","@timestamp"),
			("cpu","@cpu"),
			("event","@event"),
			("comm","@comm"),
			("pid","@pid"),
			("addr","@addr"),
			("arg0","@arg0"),
		    ("arg1","@arg1"),
		]
		self.plot.add_tools(HoverTool(tooltips=TOOLTIPS))
		# TODO: eventually rm tool?
		logging.debug('update_plot ends')
		pass
