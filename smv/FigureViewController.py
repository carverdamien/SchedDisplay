from smv.ViewController import ViewController
from functools import partial
from tornado import gen

import pandas as pd
import numpy as np

from bokeh.plotting import figure
from bokeh.events import LODEnd

import datashader as ds
import datashader.transfer_functions as tf
from datashader.bokeh_ext import InteractiveImage

# Add dummy point because datashader cannot handle emptyframe
def empty_lines():
	df = pd.DataFrame({
		'x0':[0],
		'x1':[0],
		'y0':[0],
		'y1':[0],
		'category':[0],
	})
	df['category'] = df['category'].astype('category')
	return df

# Customizable get_image_ranges:
# TODO: mv this func in app/X/__init__.py and replace it with a more generic
# because the FigureViewController should not know nr_cpu.
def get_image_ranges(FVC):
	xmin = FVC.view.x_range.start
	xmax = FVC.view.x_range.end
	w = FVC.view.plot_width
	nr_cpu = 160
	ymin = -1
	ymax = nr_cpu+1
	px_height = 4
	h = (nr_cpu+2)*px_height
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
			lines=empty_lines(), 
			get_image_ranges=get_image_ranges,
			doc=None,
			log=None,
		):
		self.lines = lines
		self.get_image_ranges = get_image_ranges
		view = figure(
			x_range=(0,1), # datashader cannot handle 0-sized range
			y_range=(0,1), # datashader cannot handle 0-sized range
		)
		super(FigureViewController, self).__init__(view, doc, log)
		# Has to be executed before inserting plot in doc
		self.view.on_event(LODEnd, self.callback_LODEnd)
		# Has to be executed before inserting plot in doc
		self.img = InteractiveImage(self.view, self.callback_InteractiveImage)

	def callback_LODEnd(self, event):
		self.update_image()

	def update_image(self):
		self.log('update_image starts')
		ranges = self.get_image_ranges(self)
		self.img.update_image(ranges)
		self.log('update_image ends')
		pass

	def callback_InteractiveImage(self, x_range, y_range, plot_width, plot_height, name=None):
		self.log('callback_InteractiveImage starts')
		cvs = ds.Canvas(
			plot_width=plot_width, plot_height=plot_height,
			x_range=x_range, y_range=y_range,
		)
		agg = cvs.line(self.lines,
			x=['x0','x1'], y=['y0','y1'],
			agg=ds.count_cat('category'), axis=1,
		)
		img = tf.shade(agg,min_alpha=255)
		self.log('callback_InteractiveImage ends')
		return img

	def plot(self, lines, width, height, xmin=None, xmax=None, ymin=None, ymax=None):
		if self.doc is not None:
			@gen.coroutine
			def coroutine():
				self._plot(lines, width, height, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
			self.doc.add_next_tick_callback(partial(coroutine))

	def _plot(self, lines, width, height, xmin=None, xmax=None, ymin=None, ymax=None):
		if xmin is None:
			xmin = min(min(lines['x0']),min(lines['x1']))
		if xmax is None:
			xmax = max(max(lines['x0']),max(lines['x1']))
		if ymin is None:
			ymin = min(min(lines['y0']),min(lines['y1']))
		if ymax is None:
			ymax = max(max(lines['y0']),max(lines['y1']))
		self.view.x_range.start = xmin
		self.view.x_range.end = xmax
		self.view.y_range.start = ymin
		self.view.y_range.end = ymax
		self.view.plot_width = width
		self.view.plot_height = height
		self.lines = lines
		self.update_image()
		pass
