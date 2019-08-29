from smv.ViewController import ViewController
from bokeh.layouts import column, row
from functools import partial
from tornado import gen
from threading import Thread

import dask
from multiprocessing import cpu_count
import pandas as pd
import numpy as np

from bokeh.plotting import figure
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

def get_image_ranges(FVC):
	xmin = FVC.fig.x_range.start
	xmax = FVC.fig.x_range.end
	ymin = FVC.fig.y_range.start
	ymax = FVC.fig.y_range.end
	w = FVC.fig.plot_width
	h = FVC.fig.plot_height
	return {
		'xmin':xmin,
		'xmax':xmax,
		'ymin':ymin,
		'ymax':ymax,
		'w':w,
		'h':h,
	}

class FigureViewController(ViewController):
	"""docstring for FigureViewController"""
	def __init__(self, 
			x_range=(0,1), # datashader cannot handle 0-sized range
			y_range=(0,1), # datashader cannot handle 0-sized range
			lines=empty_lines(), 
			get_image_ranges=get_image_ranges,
			doc=None,
			log=None,
		):
		self.query = ''
		self.lines = lines
		self.lines_to_render = lines
		self.get_image_ranges = get_image_ranges
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
		view = column(
			dropdown,
			row(legend, fig, sizing_mode='stretch_both',),
			query_textinput,
			sizing_mode='stretch_both',
		)
		super(FigureViewController, self).__init__(view, doc, log)
		self.dropdown = dropdown
		self.dropdown.on_click(self.on_click_dropdown)
		self.fig = fig
		self.legend = legend
		self.query_textinput = query_textinput
		# Has to be executed before inserting fig in doc
		self.fig.on_event(LODEnd, self.callback_LODEnd)
		# Has to be executed before inserting fig in doc
		self.color_key = datashader_color
		self.img = InteractiveImage(self.fig, self.callback_InteractiveImage)
		self.query_textinput.on_change('value', self.on_change_query_textinput)
		assert(len(self.fig.renderers) == 1)
		self.datashader = self.fig.renderers[0]
		self.source = ColumnDataSource({})
		self.segment = None
		self.hovertool = None
		self.hide_hovertool_for_category = None
		self.table = None

	def on_click_dropdown(self, new):
		if new.item == 'legend':
			self.legend.visible = not self.legend.visible
		else:
			raise Exception('Exception in on_click_dropdown: {}'.format(new.item))

	@ViewController.logFunctionCall
	def update_source(self, df):
		self.source.data = ColumnDataSource.from_df(df)
		if self.table is not None:
			self.table.columns = [TableColumn(field=c, title=c) for c in df.columns]

	def on_change_query_textinput(self, attr, old, new):
		self.query = self.query_textinput.value
		self.update_image()

	def callback_LODEnd(self, event):
		self.update_image()

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
		@gen.coroutine
		def coroutine(df):
			self.update_source(df)
		if self.doc is not None:
			self.doc.add_next_tick_callback(partial(coroutine, df))

	@ViewController.logFunctionCall
	def update_image(self):
		try:
			self._update_image()
		except Exception as e:
			self.log(e)

	def _update_image(self):
		ranges = self.get_image_ranges(self)
		self.compute_lines_to_render(ranges)
		def target():
			try:
				self.compute_hovertool(ranges)
			except Exception as e:
				print(e)
		t = Thread(target=target)
		t.start()
		self.img.update_image(ranges)
		t.join()

	@ViewController.logFunctionCall
	def apply_query(self):
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
			self.log(e)
		return self.lines

	@ViewController.logFunctionCall
	def callback_InteractiveImage(self, x_range, y_range, plot_width, plot_height, name=None):
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

	def plot(self, config, width, height, lines=empty_lines(), xmin=None, xmax=None, ymin=None, ymax=None):
		lines = dask.dataframe.from_pandas(lines, npartitions=cpu_count())
		lines.persist()
		if self.doc is not None:
			@gen.coroutine
			def coroutine():
				self._plot(config, width, height, lines=lines, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
			self.doc.add_next_tick_callback(partial(coroutine))

	@ViewController.logFunctionCall
	def _plot(self, config, width, height, lines, xmin=None, xmax=None, ymin=None, ymax=None):
		self.configure(config)
		if xmin is None:
			xmin = min(*dask.compute((lines['x0'].min(),lines['x1'].min())))
		if xmax is None:
			xmax = max(*dask.compute((lines['x0'].max(),lines['x1'].max())))
		if ymin is None:
			ymin = min(*dask.compute((lines['y0'].min(),lines['y1'].min())))
		if ymax is None:
			ymax = max(*dask.compute((lines['y0'].max(),lines['y1'].max())))
		self.fig.x_range.start = xmin
		self.fig.x_range.end = xmax
		self.fig.y_range.start = ymin
		self.fig.y_range.end = ymax
		self.fig.plot_width = width
		self.fig.plot_height = height
		self.lines = lines
		self.update_source(pd.DataFrame({k:[] for k in lines.columns}))
		glyph = Segment(
				x0='x0',
				x1='x1',
				y0='y0',
				y1='y1',
				line_alpha=0,
			)
		self.segment = self.fig.add_glyph(self.source, glyph)
		self.update_image()
		if self.hovertool is None:
			tooltips = [
				("(x,y)","($x, $y)"),
			]
			for k in lines.columns:
				tooltips.append((k,"@"+str(k)))
			self.hovertool = HoverTool(tooltips = tooltips)
			self.fig.add_tools(self.hovertool)
			# self.fig.legend.items = [LegendItem(label='Datashader', renderers=[self.datashader], index=0)]
		pass

	def configure(self, config):
		try:
			category = [c for c in config['c'] if c['len'] > 0]
			self.legend.text = '\n'.join(
				['Categories:<ul style="list-style: none;padding-left: 0;">']+
				['<li><span style="color: {};">◼</span>c[{}]={}</li>'.format(category[i]['color'], i, category[i]['label']) for i in range(len(category))]+
				["</ul>"]
			)
			msg = ['category:']+['c[{}]={}'.format(i, category[i]) for i in range(len(category))]
			self.log('\n'.join(msg))
			self.color_key = [c['color'] for c in category]
			self.hide_hovertool_for_category = [
				i
				for i in range(len(category))
				if 'hide_hovertool' in category[i]
				if category[i]['hide_hovertool']
			]
		except Exception as e:
			self.log(e)
		pass
