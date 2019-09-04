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
import traceback

from bokeh.plotting import figure
from bokeh.models.widgets import Button
from bokeh.models.widgets import TextInput
from bokeh.models.widgets import TableColumn
from bokeh.models.widgets import Div
from bokeh.models.widgets import Dropdown
from bokeh.models import ColumnDataSource
from bokeh.models.glyphs import Segment
from bokeh.models.markers import X as Marker
from bokeh.models import Legend, LegendItem
from bokeh.events import LODEnd as LODEnd_event
from bokeh.events import Reset as Reset_event
from bokeh.models.tools import HoverTool

import datashader as ds
import datashader.transfer_functions as tf
from datashader.bokeh_ext import InteractiveImage
from smv.ImageModel import PointImageModel

# datashader_color=['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999', '#66c2a5', '#fc8d62', '#8da0cb', '#a6d854', '#ffd92f', '#e5c494', '#ffffb3', '#fb8072', '#fdb462', '#fccde5', '#d9d9d9', '#ccebc5', '#ffed6f']

def customize_ranges(ranges):
	return {
		k:ranges[k]
		for k in ['xmin', 'xmax', 'ymin', 'ymax', 'w', 'h']
	}

class FigureViewController(ViewController):
	"""docstring for FigureViewController"""
	def __init__(self,
			model=PointImageModel(),
			x_range=(0,1), # datashader cannot handle 0-sized range
			y_range=(0,1), # datashader cannot handle 0-sized range
			customize_ranges=customize_ranges,
			doc=None,
			log=None,
		):
		self.query = ''
		self.model = model
		fig = figure(
			x_range=x_range,
			y_range=y_range,
			reset_policy="event_only",
			sizing_mode='stretch_both',
		)
		legend = Div(
			visible=True,
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
		options_dropdown = Dropdown(
			label='Options',
			sizing_mode='fixed',
			menu=[('Show/Hide Legend','legend'),('Enable/Disable Auto Update','auto')]
		)
		actions_dropdown = Dropdown(
			label='Actions',
			sizing_mode='fixed',
			menu=[('Fit Window','fit')],
		)
		status_button = Button(
			label='Auto Update',
			sizing_mode='fixed',
			#sizing_mode='stretch_width',
			width_policy='min',
		)
		view = column(
			row(
				options_dropdown,
				actions_dropdown,
				Spacer(sizing_mode='stretch_width', width_policy='max'),
				status_button, sizing_mode='stretch_width',
			),
			row(legend, fig, sizing_mode='stretch_both',),
			query_textinput,
			sizing_mode='stretch_both',
		)
		super(FigureViewController, self).__init__(view, doc, log)
		self.auto_update_image = True
		self.options_dropdown = options_dropdown
		self.options_dropdown.on_click(self.on_click_options_dropdown)
		self.actions_dropdown = actions_dropdown
		self.actions_dropdown.on_click(self.on_click_actions_dropdown)
		self.status_button = status_button
		self.status_button.on_click(self.on_click_status_button)
		self.fig = fig
		self.legend = legend
		self.query_textinput = query_textinput
		# Has to be executed before inserting fig in doc
		self.fig.on_event(LODEnd_event, self.callback_LODEnd)
		# Has to be executed before inserting fig in doc
		self.fig.on_event(Reset_event, self.callback_Reset)
		# Has to be executed before inserting fig in doc
		# self.color_key = datashader_color
		self.img = Queue(maxsize=1)
		self.interactiveImage = InteractiveImage(self.fig, self.callback_InteractiveImage)
		self.user_lock = Lock()
		# Forbid widget changes when busy
		self.user_widgets = [
			self.query_textinput,
			self.status_button,
			self.options_dropdown,
			self.actions_dropdown,
		]
		self.query_textinput.on_change('value', self.on_change_query_textinput)
		assert(len(self.fig.renderers) == 1)
		self.datashader = self.fig.renderers[0]
		self.source = ColumnDataSource({})
		self.hovertool = None
		self.hide_hovertool_for_category = None
		self.table = None

	#######################################
	# Functions triggered by User actions #
	#######################################

	def on_click_status_button(self, new):
		fname = self.on_click_status_button.__name__
		if not self.user_lock.acquire(False):
			self.log('Could not acquire user_lock in {}'.format(fname))
			return
		def target():
			try:
				self.set_busy()
				self.update_image()
				self.set_update()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
				self.set_failed()
			else:
				self.user_lock.release()
		Thread(target=target).start()

	def on_click_actions_dropdown(self, new):
		if new.item == 'fit':
			self.action_fit_window()
			pass
		else:
			raise Exception('Exception in on_click_actions_dropdown: {}'.format(new.item))

	def on_click_options_dropdown(self, new):
		# Very short, no need to spawn a Thread
		if new.item == 'legend':
			self.legend.visible = not self.legend.visible
		elif new.item == 'auto':
			self.auto_update_image = not self.auto_update_image
		else:
			raise Exception('Exception in on_click_options_dropdown: {}'.format(new.item))
		pass

	def action_fit_window(self):
		fname = self.fit_window.__name__
		if not self.user_lock.acquire(False):
			self.log('Could not acquire user_lock in {}'.format(fname))
			return
		def target():
			try:
				self.set_busy()
				xmin, xmax, ymin, ymax = self.model.result_ranges()
				self.fit_window(xmin, xmax, ymin, ymax)
				self.set_update()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
				self.set_failed()
			else:
				self.user_lock.release()
		Thread(target=target).start()


	def plot(self, **kwargs):
		fname = self.plot.__name__
		if not self.user_lock.acquire(False):
			self.log('Could not acquire user_lock in {}'.format(fname))
			return
		def target(model=None, config=None, width=None, height=None):
			try:
				self.set_busy()
				self.model = model
				xmin, xmax, ymin, ymax = self.model.data_ranges()
				self._plot(config, width, height, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
				self.set_update()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
				self.set_failed()
			else:
				self.user_lock.release()
		Thread(target=target, kwargs=kwargs).start()

	def on_change_query_textinput(self, attr, old, new):
		fname = self.on_change_query_textinput.__name__
		if not self.user_lock.acquire(False):
			self.log('Could not acquire user_lock in {}'.format(fname))
			return
		def target():
			try:
				self.set_busy()
				self.query = self.query_textinput.value
				if self.auto_update_image:
					self.update_image()
				self.set_update()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
				self.set_failed()
			else:
				self.user_lock.release()
		Thread(target=target).start()

	def callback_LODEnd(self, event):
		fname = self.callback_LODEnd.__name__
		if not self.auto_update_image:
			return
		if not self.user_lock.acquire(False):
			self.log('Could not acquire user_lock in {}'.format(fname))
			return
		def target():
			try:
				self.set_busy()
				self.update_image()
				self.set_update()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
				self.set_failed()
			else:
				self.user_lock.release()
		Thread(target=target).start()

	def callback_Reset(self, event):
		fname = self.callback_Reset.__name__
		if not self.user_lock.acquire(False):
			self.log('Could not acquire user_lock in {}'.format(fname))
			return
		def target():
			try:
				self.set_busy()
				xmin, xmax, ymin, ymax = self.model.data_ranges()
				self.fit_window(xmin, xmax, ymin, ymax)
				self.update_image(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
				self.set_update()
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
				self.set_failed()
			else:
				self.user_lock.release()
		Thread(target=target).start()

	####################################
	# Functions modifying the document #
	####################################

	# Try to avoid intensive computation
	# Must use coroutine

	def fit_window(self, xmin, xmax, ymin, ymax):
		@gen.coroutine
		def coroutine(xmin, xmax, ymin, ymax):
			self.fig.x_range.start = xmin
			self.fig.x_range.end = xmax
			self.fig.y_range.start = ymin
			self.fig.y_range.end = ymax
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine, xmin, xmax, ymin, ymax))

	def set_failed(self):
		@gen.coroutine
		def coroutine():
			for e in self.user_widgets:
				e.disabled= False
			self.visible = True
			self.status_button.label = "Failed"
			self.status_button.button_type = "failure"
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine))

	def set_busy(self):
		@gen.coroutine
		def coroutine():
			for e in self.user_widgets:
				e.disabled= True
			self.visible = True
			self.status_button.label = "Busy"
			self.status_button.button_type = "warning"
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine))

	def set_update(self):
		@gen.coroutine
		def coroutine():
			for e in self.user_widgets:
				e.disabled= False
			self.visible = True
			if self.auto_update_image:
				self.status_button.label = "Auto Update"
			else:
				self.status_button.label = "Update"
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
			category = config['c']
			self.legend.text = '\n'.join(
				['Categories:<ul style="list-style: none;padding-left: 0;">']+
				[
					'<li><span style="color: {};">◼</span>c[{}]={}</li>'.format(
						category[i]['color'],
						i,
						category[i]['label']
					)
					for i in range(len(category))
					if category[i]['len'] > 0
				]+
				["</ul>"]
			)
			# self.color_key = [c['color'] for c in category if c['len'] > 0]
			self.hide_hovertool_for_category = [
				i
				for i in range(len(category))
				if 'hide_hovertool' in category[i]
				if category[i]['hide_hovertool']
			]
			df = self.model.data
			_df = pd.DataFrame({k:[] for k in df.columns})
			self.source.data = ColumnDataSource.from_df(_df)
			if self.table is not None:
				self.table.columns = [TableColumn(field=c, title=c) for c in _df.columns]
			glyph = self.model.bokeh_glyph()
			renderer = self.fig.add_glyph(self.source, glyph)
			if self.hovertool is None:
				tooltips = [
					("(x,y)","($x, $y)"),
				]
				for k in df.columns:
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
			self.log(traceback.format_exc())
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
		if self.mode == 'lines':
			no_query = self.lines
		elif self.mode == 'points':
			no_query = self.points
		else:
			raise Exception('Not Yet Implemented')
		try:
			if self.query.strip() == '':
				return no_query
			self.log('Applying query {}'.format(self.query))
			query = no_query.query(self.query)
			if len(query) == 0:
				raise Exception(
					'QUERY ERROR',
					'{} => len(lines) == 0'.format(self.query)
				)
			return query
		except Exception as e:
			self.log('Exception({}) in {}: {}'.format(type(e), fname, e))
			self.log(traceback.format_exc())
		return no_query

	@ViewController.logFunctionCall
	def _callback_InteractiveImage(self, *args, **kwargs):
		return self.model.callback_InteractiveImage(*args, **kwargs)

	@ViewController.logFunctionCall
	def compute_hovertool(self, ranges):
		MAX = 100000.
		xmin = ranges['xmin']
		xmax = ranges['xmax']
		ymin = ranges['ymin']
		ymax = ranges['ymax']
		intersection = self.model.generate_intersection_query(xmin, xmax, ymin, ymax)
		if len(self.hide_hovertool_for_category)==0:
			query = intersection
		else:
			hide_hovertool = "&".join([
				"(c!={})".format(c)
				for c in self.hide_hovertool_for_category
			])
			query = "({})&({})".format(intersection, hide_hovertool)
		self.log("HoverTool query={}".format(query))
		result = self.model.result.query(query)
		n = len(result)
		if n > MAX:
			frac = MAX/n
			self.log('Sampling hovertool frac={}'.format(frac))
			result = result.sample(frac=frac)
		else:
			self.log('Full hovertool')
		df = dask.compute(result)[0]
		self.update_source(df)

	@ViewController.logFunctionCall
	def update_image(self, **kwargs):
		ranges = {
			'xmin' : self.fig.x_range.start,
			'xmax' : self.fig.x_range.end,
			'ymin' : self.fig.y_range.start,
			'ymax' : self.fig.y_range.end,
			'w' : self.fig.plot_width,
			'h' : self.fig.plot_height,
		}
		for k in ['xmin', 'xmax', 'ymin', 'ymax', 'w', 'h']:
			if k in kwargs:
				ranges[k] = kwargs[k]
		ranges = self.customize_ranges(ranges)
		self.model.apply_query(self.query)
		def target0():
			try:
				self.compute_hovertool(ranges)
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e),target0.__name__,e))
				self.log(traceback.format_exc())
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
				self.log(traceback.format_exc())
		threads = [Thread(target=target0), Thread(target=target1)]
		for t in threads:
			t.start()
		for t in threads:
			t.join()
		self.fit_figure(ranges)
