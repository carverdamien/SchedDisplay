from smv.ViewController import ViewController
from bokeh.layouts import column, row, Spacer
from functools import partial
from tornado import gen
from threading import Thread, Lock
from queue import Queue

import dask
from multiprocessing import cpu_count
import pandas as pd
import numpy as np

from bokeh.plotting import figure
from bokeh.models.widgets import Button
from bokeh.models.widgets import TextInput
from bokeh.models.widgets import TableColumn
from bokeh.models.widgets import Div
from bokeh.models.widgets import Dropdown
from bokeh.models import ColumnDataSource
from bokeh.models.glyphs import Segment
from bokeh.models import Legend, LegendItem
from bokeh.events import LODEnd
from bokeh.models.tools import HoverTool

import datashader as ds
import datashader.transfer_functions as tf
from datashader.bokeh_ext import InteractiveImage

datashader_color=['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999', '#66c2a5', '#fc8d62', '#8da0cb', '#a6d854', '#ffd92f', '#e5c494', '#ffffb3', '#fb8072', '#fdb462', '#fccde5', '#d9d9d9', '#ccebc5', '#ffed6f']

# Add dummy point because datashader cannot handle emptyframe
def empty_lines():
	df = pd.DataFrame({
		'x0':[0, 1],
		'x1':[0, 1],
		'y0':[0, 1],
		'y1':[0, 1],
		'c':[0, 1],
	})
	df['c'] = df['c'].astype('category')
	return df

def customize_ranges(ranges):
	return {
		k:ranges[k]
		for k in ['xmin', 'xmax', 'ymin', 'ymax', 'w', 'h']
	}

class FigureViewController(ViewController):
	"""docstring for FigureViewController"""
	def __init__(self, 
			x_range=(0,1), # datashader cannot handle 0-sized range
			y_range=(0,1), # datashader cannot handle 0-sized range
			lines=empty_lines(), 
			customize_ranges=customize_ranges,
			doc=None,
			log=None,
		):
		self.query = ''
		self.lines = lines
		self.lines_to_render = lines
		self.customize_ranges = customize_ranges
		fig = figure(
			x_range=x_range,
			y_range=y_range,
			sizing_mode='stretch_both',
		)
		legend = Div(
			visible=False,
			width_policy='min',
			height_policy='max',
		)
		# fig.add_layout(Legend(click_policy='hide'))
		query_textinput = TextInput(
			title="query",
			sizing_mode="stretch_width",
			value='',
			width=100
		)
		dropdown = Dropdown(
			label='Options',
			sizing_mode='fixed',
			menu=[('Show/Hide Legend','legend')]
		)
		status_button = Button(
			label='Done',
			sizing_mode='fixed',
			#sizing_mode='stretch_width',
			width_policy='min',
		)
		view = column(
			row(dropdown, Spacer(sizing_mode='stretch_width', width_policy='max'), status_button, sizing_mode='stretch_width',),
			row(legend, fig, sizing_mode='stretch_both',),
			query_textinput,
			sizing_mode='stretch_both',
		)
		super(FigureViewController, self).__init__(view, doc, log)
		self.dropdown = dropdown
		self.dropdown.on_click(self.on_click_dropdown)
		self.status_button = status_button
		self.fig = fig
		self.legend = legend
		self.query_textinput = query_textinput
		# Has to be executed before inserting fig in doc
		self.fig.on_event(LODEnd, self.callback_LODEnd)
		# Has to be executed before inserting fig in doc
		self.color_key = datashader_color
		self.img = Queue(maxsize=1)
		self.interactiveImage = InteractiveImage(self.fig, self.callback_InteractiveImage)
		self.user_lock = Lock()
		self.query_textinput.on_change('value', self.on_change_query_textinput)
		assert(len(self.fig.renderers) == 1)
		self.datashader = self.fig.renderers[0]
		self.source = ColumnDataSource({})
		self.segment = None
		self.hovertool = None
		self.hide_hovertool_for_category = None
		self.table = None

	#######################################
	# Functions triggered by User actions #
	#######################################

	# Forbid user to trigger more than one action

	def on_click_dropdown(self, new):
		# Very short, no need to spawn a Thread
		if new.item == 'legend':
			self.legend.visible = not self.legend.visible
		else:
			raise Exception('Exception in on_click_dropdown: {}'.format(new.item))

	# TODO decorator

	def plot(self, config, width, height, lines=empty_lines(), xmin=None, xmax=None, ymin=None, ymax=None):
		fname = self.plot.__name__
		if not self.user_lock.acquire(False):
			self.log('Could not acquire user_lock in {}'.format(fname))
			return
		def target(config, width, height, lines, xmin, xmax, ymin, ymax):
			try:
				self.set_busy()
				lines = dask.dataframe.from_pandas(lines, npartitions=cpu_count())
				lines.persist()
				self.lines = lines
				self.lines_to_render = lines
				if xmin is None:
					xmin = min(*dask.compute((self.lines['x0'].min(),self.lines['x1'].min())))
				if xmax is None:
					xmax = max(*dask.compute((self.lines['x0'].max(),self.lines['x1'].max())))
				if ymin is None:
					ymin = min(*dask.compute((self.lines['y0'].min(),self.lines['y1'].min())))
				if ymax is None:
					ymax = max(*dask.compute((self.lines['y0'].max(),self.lines['y1'].max())))
				self._plot(config, width, height, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
				self.set_done()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.set_failed()
			else:
				self.user_lock.release()
		args = config, width, height, lines, xmin, xmax, ymin, ymax
		Thread(target=target, args=args).start()

	def on_change_query_textinput(self, attr, old, new):
		fname = self.on_change_query_textinput.__name__
		if not self.user_lock.acquire(False):
			self.log('Could not acquire user_lock in {}'.format(fname))
			return
		def target():
			try:
				self.set_busy()
				self.query = self.query_textinput.value
				self.update_image()
				self.set_done()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.set_failed()
			else:
				self.user_lock.release()
		Thread(target=target).start()

	def callback_LODEnd(self, event):
		fname = self.callback_LODEnd.__name__
		if not self.user_lock.acquire(False):
			self.log('Could not acquire user_lock in {}'.format(fname))
			return
		def target():
			try:
				self.set_busy()
				self.update_image()
				self.set_done()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.set_failed()
			else:
				self.user_lock.release()
		Thread(target=target).start()

	####################################
	# Functions modifying the document #
	####################################

	# Try to avoid intensive computation
	# Must use coroutine

	def set_failed(self):
		@gen.coroutine
		def coroutine():
			self.visible = True
			self.status_button.label = "Failed"
			self.status_button.button_type = "failure"
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine))

	def set_busy(self):
		@gen.coroutine
		def coroutine():
			self.visible = True
			self.status_button.label = "Busy"
			self.status_button.button_type = "warning"
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine))


	def set_done(self):
		@gen.coroutine
		def coroutine():
			self.visible = True
			self.status_button.label = "Done"
			self.status_button.button_type = "success"
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine))

	@ViewController.logFunctionCall
	def _plot(self, config, width, height, xmin, xmax, ymin, ymax):
		@gen.coroutine
		def coroutine(config, width, height, xmin, xmax, ymin, ymax):
			self.fig.x_range.start = xmin
			self.fig.x_range.end = xmax
			self.fig.y_range.start = ymin
			self.fig.y_range.end = ymax
			self.fig.plot_width = width
			self.fig.plot_height = height
			category = [c for c in config['c'] if c['len'] > 0]
			self.legend.text = '\n'.join(
				['Categories:<ul style="list-style: none;padding-left: 0;">']+
				['<li><span style="color: {};">◼</span>c[{}]={}</li>'.format(category[i]['color'], i, category[i]['label']) for i in range(len(category))]+
				["</ul>"]
			)
			self.color_key = [c['color'] for c in category]
			self.hide_hovertool_for_category = [
				i
				for i in range(len(category))
				if 'hide_hovertool' in category[i]
				if category[i]['hide_hovertool']
			]
			df = pd.DataFrame({k:[] for k in self.lines.columns})
			self.source.data = ColumnDataSource.from_df(df)
			if self.table is not None:
				self.table.columns = [TableColumn(field=c, title=c) for c in df.columns]
			glyph = Segment(
				x0='x0',
				x1='x1',
				y0='y0',
				y1='y1',
				line_alpha=0,
			)
			self.segment = self.fig.add_glyph(self.source, glyph)
			if self.hovertool is None:
				tooltips = [
					("(x,y)","($x, $y)"),
				]
				for k in self.lines.columns:
					tooltips.append((k,"@"+str(k)))
				self.hovertool = HoverTool(tooltips = tooltips)
				self.fig.add_tools(self.hovertool)
			self.update_image()
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine, config, width, height, xmin, xmax, ymin, ymax))

	@ViewController.logFunctionCall
	def update_source(self, df):
		@gen.coroutine
		def coroutine(df):
			self.source.data = ColumnDataSource.from_df(df)
			if self.table is not None:
				self.table.columns = [TableColumn(field=c, title=c) for c in df.columns]
		if self.doc is not None:
			self.doc.add_next_tick_callback(partial(coroutine, df))

	@ViewController.logFunctionCall
	def callback_InteractiveImage(self, x_range, y_range, plot_width, plot_height, name=None):
		fname = self.callback_InteractiveImage.__name__
		try:
			img = self.img.get(block=False)
		except Exception as e:
			self.log('Exception({}) in {}: {}'.format(type(e), fname, e))
			img = self._callback_InteractiveImage(x_range, y_range, plot_width, plot_height, name)
		return img

	@ViewController.logFunctionCall
	def fit_figure(self, ranges):
		@gen.coroutine
		def coroutine(ranges):
			self.fig.x_range.start = ranges['xmin']
			self.fig.x_range.end = ranges['xmax']
			self.fig.y_range.start = ranges['ymin']
			self.fig.y_range.end = ranges['ymax']
			self.fig.plot_width = ranges['w']
			self.fig.plot_height = ranges['h']
		if self.doc is not None:
			self.doc.add_next_tick_callback(partial(coroutine, ranges))

	###############################
	# Compute intensive functions #
	###############################

	# Should not be ran in the interactive thread

	@ViewController.logFunctionCall
	def apply_query(self):
		fname = self.apply_query.__name__
		try:
			if self.query.strip() == '':
				return self.lines
			self.log('Applying query {}'.format(self.query))
			lines = self.lines.query(self.query)
			if len(lines) == 0:
				raise Exception(
					'QUERY ERROR',
					'{} => len(lines) == 0'.format(self.query)
				)
			return lines
		except Exception as e:
			self.log('Exception({}) in {}: {}'.format(type(e), fname, e))
		return self.lines

	@ViewController.logFunctionCall
	def _callback_InteractiveImage(self, x_range, y_range, plot_width, plot_height, name=None):
		cvs = ds.Canvas(
			plot_width=plot_width, plot_height=plot_height,
			x_range=x_range, y_range=y_range,
		)
		agg = cvs.line(self.lines_to_render,
			x=['x0','x1'], y=['y0','y1'],
			agg=ds.count_cat('c'), axis=1,
		)
		img = tf.shade(agg,min_alpha=255,color_key=self.color_key)
		return img

	@ViewController.logFunctionCall
	def compute_lines_to_render(self, ranges):
		self.lines_to_render = self.lines
		self.lines_to_render = self.apply_query()

	@ViewController.logFunctionCall
	def compute_hovertool(self, ranges):
		MAX = 100000.
		xmin = ranges['xmin']
		xmax = ranges['xmax']
		xspatial = "({})|({})|({})".format(
			"x0>={} & x0<={}".format(xmin,xmax),
			"x1>={} & x1<={}".format(xmin,xmax),
			"x0<={} & x1>={}".format(xmin,xmax),
		)
		ymin = ranges['ymin']
		ymax = ranges['ymax']
		yspatial = "({})|({})|({})".format(
			"y0>={} & y0<={}".format(ymin,ymax),
			"y1>={} & y1<={}".format(ymin,ymax),
			"y0<={} & y1>={}".format(ymin,ymax),
		)
		spatial = "({})&({})".format(xspatial, yspatial)
		if len(self.hide_hovertool_for_category)==0:
			query = spatial
		else:
			hide_hovertool = "&".join([
				"(c!={})".format(c)
				for c in self.hide_hovertool_for_category
			])
			query = "({})&({})".format(spatial, hide_hovertool)
		self.log("HoverTool query={}".format(query))
		lines_to_render = self.lines_to_render.query(query)
		n = len(lines_to_render)
		if n > MAX:
			frac = MAX/n
			self.log('Sampling hovertool frac={}'.format(frac))
			lines_to_render = lines_to_render.sample(frac=frac)
		else:
			self.log('Full hovertool')
		df = dask.compute(lines_to_render)[0]
		self.update_source(df)

	@ViewController.logFunctionCall
	def update_image(self):
		ranges = {
			'xmin' : self.fig.x_range.start,
			'xmax' : self.fig.x_range.end,
			'ymin' : self.fig.y_range.start,
			'ymax' : self.fig.y_range.end,
			'w' : self.fig.plot_width,
			'h' : self.fig.plot_height,
		}
		ranges = self.customize_ranges(ranges)
		self.compute_lines_to_render(ranges)
		def target0():
			try:
				self.compute_hovertool(ranges)
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e),target0.__name__,e))
		def target1():
			try:
				xmin, xmax, ymin, ymax, w, h = [
					ranges[k] for k in ['xmin', 'xmax', 'ymin', 'ymax', 'w', 'h']
				]
				self.log(ranges) # debug
				self.img.put(self._callback_InteractiveImage((xmin,xmax), (ymin,ymax), w, h))
				@gen.coroutine
				def coroutine():
					self.interactiveImage.update_image(ranges)
				if self.doc:
					self.doc.add_next_tick_callback(partial(coroutine))
			except Exception as e:
				 self.log('Exception({}) in {}:{}'.format(type(e),target1.__name__,e))
		threads = [Thread(target=target0), Thread(target=target1)]
		for t in threads:
			t.start()
		for t in threads:
			t.join()
		self.fit_figure(ranges)
