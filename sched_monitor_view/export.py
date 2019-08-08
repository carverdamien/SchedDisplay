import sched_monitor_view.bg.loadDataFrame
import sched_monitor_view.lang.filter
import sched_monitor_view.lang.columns

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import itertools

def export(img_path, json_dict):
	print(img_path, json_dict)
	hdf5_path = json_dict['hdf5'][0]
	path_id = 0
	def callback_load_hdf5(path, data, done):
		df = data['df']
		compute_columns(df, json_dict['columns'])
		update_plot(df, json_dict['renderers'])
		# print(df)
	def done():
		pass
	sched_monitor_view.bg.loadDataFrame.fg(hdf5_path, path_id, callback_load_hdf5, done)

def compute_columns(df, columns):
	for column in columns:
		df[column] = sched_monitor_view.lang.columns.compute(
			df,
			columns[column],
		)
	pass

def update_plot(df, renderers):
	fig, ax = plt.subplots()
	# lines = [[(0, 1), (1, 1)], [(2, 3), (3, 3)], [(1, 2), (1, 3)]]
	# c     = np.array([(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)])
	# lc    = LineCollection(lines, colors=c, linewidths=2)
	xmin = 0
	xmax = df['timestamp'].iloc[-1]
	ymin = 0 - 1
	ymax = 159 + 1
	for r in renderers:
		# lines = [
		# 	[p0,p1]
		# 	for p0, p1 in itertools.zip_longest(
		# 		[
		# 			(x0,y0)
		# 			for x0, y0 in itertools.zip_longest(df[r['x0']],df[r['y0']])
		# 		],
		# 		[	
		# 			(x1,y1)
		# 			for x1, y1 in itertools.zip_longest(df[r['x1']],df[r['y1']])
		# 		],
		# 	)
		# ]
		X0 = np.array([xmin])
		X1 = np.array([xmax])
		Y0 = np.array([ymin])
		Y1 = np.array([ymax])
		lines = [
			[p0,p1]
			for p0, p1 in itertools.zip_longest(
				[
					(x0,y0)
					for x0, y0 in itertools.zip_longest(X0,Y0)
				],
				[	
					(x1,y1)
					for x1, y1 in itertools.zip_longest(X1,Y1)
				],
			)
		]
		L = np.array([[X0,Y0],[X1,Y1]])
		N = 1
		L = np.reshape(L, (N,2,2))
		print('lines=',lines)
		print('L=',L)
		# x = np.arange(100)
		# # Here are many sets of y to plot vs x
		# ys = x[:50, np.newaxis] + x[np.newaxis, :]
		# segs = np.zeros((50, 100, 2))
		# segs[:, :, 1] = ys
		# segs[:, :, 0] = x
		# L = segs
		lc = LineCollection(L)
		ax.add_collection(lc)
	ax.set_xlim(xmin, xmax)
	ax.set_ylim(ymin, ymax)
	fig.savefig('foo.jpg')
	pass