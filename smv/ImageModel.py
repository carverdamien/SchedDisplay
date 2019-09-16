import dask
import traceback
import pandas as pd
import datashader as ds
import datashader.transfer_functions as tf
from bokeh.models.glyphs import Segment
from bokeh.models.markers import X as Marker
from multiprocessing import cpu_count
from bokeh.models import ColumnDataSource
from string import Template

QUERY_SUBSTITUTE = {
	'EXEC_EVT'    : '0',
	'EXIT_EVT'    : '1',
	'WAKEUP'      : '2',
	'WAKEUP_NEW'  : '3',
	'BLOCK'       : '4',
	'BLOCK_IO'    : '5',
	'BLOCK_LOCK'  : '6',
	'WAKEUP_LOCK' : '7',
	'WAKER_LOCK'  : '8',
	'FORK_EVT'    : '9',
	'TICK_EVT'    : '10',
	'CTX_SWITCH'  : '11',
	'MIGRATE_EVT' : '12',
	'RQ_SIZE'     : '13',
	'IDLE_BALANCE_BEG' : '14',
	'IDLE_BALANCE_END' : '15',
	'PERIODIC_BALANCE_BEG' : '16',
	'PERIODIC_BALANCE_END' : '17',
}

class AbstractImageModel(Exception):
	pass

class QueryNoResult(Exception):
	pass

class ImageModel(object):
	"""docstring for ImageModel"""
	def __init__(self, **kwargs):
		super(ImageModel, self).__init__()
		self.category = kwargs.get('category',[{'label':'c0','color':'#000000','len':1},{'label':'c1','color':'#ffffff','len':1}])
		data = kwargs.get('data', self.generate_empty_data())
		self.data = dask.dataframe.from_pandas(data, npartitions=cpu_count()) 
		self.query = ''
		self.query_substitute = kwargs.get('query_substitute', QUERY_SUBSTITUTE)
		self.result = kwargs.get('result', self.data)
		self.log = kwargs.get('log', print)
		self.color_key =  [c['color'] for c in self.category if c['len'] > 0]
		self.callback_apply_query = []

	def bokeh_glyph(self):
		raise AbstractImageModel()

	def generate_empty_data(self):
		raise AbstractImageModel()

	def data_ranges(self):
		raise AbstractImageModel()
	
	def result_ranges(self):
		raise AbstractImageModel()

	def generate_intersection_query(self, xmin, xmax, ymin, ymax):
		raise AbstractImageModel()

	def on_apply_query(self, callback):
		self.callback_apply_query.append(callback)

	def apply_query(self, query):
		self.query = Template(query).substitute(**self.query_substitute)
		self.result = self.data
		if self.query.strip() != '':
			try:
				self.log('Applying query {}'.format(self.query))
				result = self.data.query(self.query)
				if len(result) == 0:
					raise QueryNoResult(self.query)
				self.result = result
			except Exception as e:
				# Note: This does not only catches QueryNoResult
				self.log('Exception({}): {}'.format(type(e), e))
				self.log(traceback.format_exc())
		for callback in self.callback_apply_query:
			callback(data=self.result, query=self.query)
		return

class PointImageModel(ImageModel):
	"""docstring for PointImageModel"""
	def __init__(self, **kwarg):
		super(PointImageModel, self).__init__(**kwarg)

	def bokeh_glyph(self):
		return Marker(
			x='x',
			y='y',
			line_alpha=0,
		)

	def generate_empty_data(self):
		df = pd.DataFrame({
			'x':[0,1],
			'y':[0,1],
			'c':[0,1],
		})
		df['c'] = df['c'].astype('category')
		return df
	
	def data_ranges(self):
		xmin = dask.compute(self.data['x'].min())[0]
		xmax = dask.compute(self.data['x'].max())[0]
		ymin = dask.compute(self.data['y'].min())[0]
		ymax = dask.compute(self.data['y'].max())[0]
		return xmin, xmax, ymin, ymax

	def result_ranges(self):
		xmin = dask.compute(self.result['x'].min())[0]
		xmax = dask.compute(self.result['x'].max())[0]
		ymin = dask.compute(self.result['y'].min())[0]
		ymax = dask.compute(self.result['y'].max())[0]
		return xmin, xmax, ymin, ymax

	def generate_intersection_query(self, xmin, xmax, ymin, ymax):
		x = f"x>={xmin} & x<={xmax}"
		y = f"y>={ymin} & y<={ymax}"
		return f"({x})&({y})"

	def callback_InteractiveImage(self, x_range, y_range, plot_width, plot_height, name=None):
		cvs = ds.Canvas(
			plot_width=plot_width, plot_height=plot_height,
			x_range=x_range, y_range=y_range,
		)
		agg = cvs.points(self.result,
			'x','y',
			agg=ds.count_cat('c'),
		)
		img = tf.shade(agg, min_alpha=255, color_key=self.color_key)
		return img

class SegmentImageModel(ImageModel):
	"""docstring for SegmentImageModel"""
	def __init__(self, **kwarg):
		super(SegmentImageModel, self).__init__(**kwarg)
	
	def bokeh_glyph(self):
		return Segment(
			x0='x0',
			x1='x1',
			y0='y0',
			y1='y1',
			line_alpha=0,
		)

	def generate_empty_data(sef):
		df = pd.DataFrame({
			'x0':[0, 1],
			'x1':[0, 1],
			'y0':[0, 1],
			'y1':[0, 1],
			'c':[0, 1],
		})
		df['c'] = df['c'].astype('category')
		return df

	def data_ranges(self):
		xmin = min(*dask.compute((self.data['x0'].min(),self.data['x1'].min())))
		xmax = max(*dask.compute((self.data['x0'].max(),self.data['x1'].max())))
		ymin = min(*dask.compute((self.data['y0'].min(),self.data['y1'].min())))
		ymax = max(*dask.compute((self.data['y0'].max(),self.data['y1'].max())))
		return xmin, xmax, ymin, ymax

	def result_ranges(self):
		xmin = min(*dask.compute((self.result['x0'].min(),self.result['x1'].min())))
		xmax = max(*dask.compute((self.result['x0'].max(),self.result['x1'].max())))
		ymin = min(*dask.compute((self.result['y0'].min(),self.result['y1'].min())))
		ymax = max(*dask.compute((self.result['y0'].max(),self.result['y1'].max())))
		return xmin, xmax, ymin, ymax

	def generate_intersection_query(self, xmin, xmax, ymin, ymax):
		x0_in = f"x0>={xmin} & x0<={xmax}"
		x1_in = f"x0>={xmin} & x0<={xmax}"
		x_out = f"x0<={xmin} & x1>={xmax}"
		x = f"({x0_in})|({x1_in})|({x_out})"
		y0_in = f"y0>={ymin} & y0<={ymax}"
		y1_in = f"y0>={ymin} & y0<={ymax}"
		y_out = f"y0<={ymin} & y1>={ymax}"
		y = f"({y0_in})|({y1_in})|({y_out})"
		return f"({x})&({y})"

	def callback_InteractiveImage(self, x_range, y_range, plot_width, plot_height, name=None):
		cvs = ds.Canvas(
			plot_width=plot_width, plot_height=plot_height,
			x_range=x_range, y_range=y_range,
		)
		agg = cvs.line(self.result,
			x=['x0','x1'], y=['y0','y1'],
			agg=ds.count_cat('c'), axis=1,
		)
		img = tf.shade(agg, min_alpha=255, color_key=self.color_key)
		return img
