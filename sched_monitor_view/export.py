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
	# df = df.iloc[np.arange(100000)]
	print(df)
	fig, ax = plt.subplots()
	# lines = [[(0, 1), (1, 1)], [(2, 3), (3, 3)], [(1, 2), (1, 3)]]
	# c     = np.array([(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)])
	# lc    = LineCollection(lines, colors=c, linewidths=2)
	xmin = 0
	xmax = df['timestamp'].iloc[-1]
	ymin = 0 - 1
	ymax = 159 + 1
	for r in renderers:
		X0 = df[r['x0']]
		X1 = df[r['x1']]
		Y0 = df[r['y0']]
		Y1 = df[r['y1']]
		N = len(X0)
		print('transpose starts')
		L = np.transpose(np.array([[X0,X1],[Y0,Y1]]))
		print('transpose ends')
		print('LineCollection starts')
		lc = LineCollection(L)
		print('LineCollection ends')
		print('add_collection starts')
		ax.add_collection(lc)
		print('add_collection ends')
	ax.set_xlim(xmin, xmax)
	ax.set_ylim(ymin, ymax)
	print('savefig starts')
	fig.savefig('foo.jpg')
	print('savefig ends')
	pass