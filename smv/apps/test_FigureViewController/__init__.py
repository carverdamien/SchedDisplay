from smv.FigureViewController import FigureViewController
import pandas as pd
import numpy as np
import dask
from multiprocessing import cpu_count
from smv.DataDict import to_tar

def dummy_lines():
	px_height = 4
	y0_shift = 0. / float(px_height)
	y1_shift = 2. / float(px_height)
	# N = 50000000
	N = 100000
	# N = 100
	tmax = 1000000000
	nr_cpu = 160
	nr_event = 20
	x0 = np.random.randint(0,tmax,N).astype(float)
	x1 = x0
	y0 = np.random.randint(0,nr_cpu,N).astype(float)
	y1 = y0 + y1_shift
	y0 = y0 + y0_shift
	c = np.random.randint(0,nr_event,N)
	df = pd.DataFrame({
		'x0':x0,
		'x1':x1,
		'y0':y0,
		'y1':y1,
		'c':c,
	})
	df['c'] = df['c'].astype('category')
	df.sort_values(by='x0', inplace=True)
	df.index = np.arange(len(df))
	# to_tar('dummy.tar', pd.DataFrame({
	# 	'timestamp' : x0,
	# 	'cpu' : y0,
	# 	'event' : c
	# }))
	df = dask.dataframe.from_pandas(df, npartitions=cpu_count())
	df.persist() # Persist multiple Dask collections into memory
	return df

def get_image_ranges(FVC):
	xmin = FVC.fig.x_range.start
	xmax = FVC.fig.x_range.end
	w = FVC.fig.plot_width
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

def modify_doc(doc):
	lines = dummy_lines()
	figure = FigureViewController(
		x_range=(0,1000000000),
		y_range=(-1,160),
		lines=lines,
		get_image_ranges=get_image_ranges,
		doc=doc)
	figure.view.sizing_mode = 'stretch_both'
	doc.add_root(figure.view)
	pass

