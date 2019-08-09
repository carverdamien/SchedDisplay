import sched_monitor_view.bg.loadDataFrame
import sched_monitor_view.lang.filter
import sched_monitor_view.lang.columns

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.ticker import MultipleLocator
import numpy as np
import itertools
import os

import matplotlib as mpl
font = { 'size' : 20,}
mpl.rc('font', **font)

def export(img_path, json_dict, hdf5_path=None):
	print(img_path, json_dict)
	if hdf5_path is None:
		hdf5_path = json_dict['hdf5'][0]
	path_id = 0
	def callback_load_hdf5(path, data, done):
		df = data['df']
		compute_columns(df, json_dict['columns'])
		plot(img_path, df, json_dict['renderers'])
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

def plot(img, df, renderers):
	figsize = (6.4*4, 4.8*1.)
	xmin = 0
	xmax = df['timestamp'].iloc[-1]
	ymin = 0 - 1
	ymax = 160 + 1
	yticks = np.arange(0,161,20)
	xminortick = None
	xmajortick = None
	if img == 'freqdelay.png':
		figsize = (6.4*1., 4.8*1.)
		center = 1 * 10**9
		size   = 0.5 * 10**8
		xmin = center - size
		xmax = center + size
		sel = (df['timestamp'] >= xmin) & (df['timestamp'] <= xmax)
		df = df[sel]
		ymin = 50
		ymax = 100
		yticks = np.arange(ymin,ymax,10)
		pass
	elif img == 'forkwait.png':
		figsize = (6.4*1., 4.8*1.)
		center = 1 * 10**9
		size   = 0.5 * 10**8
		xmin = center - size
		xmax = center + size
		sel = (df['timestamp'] >= xmin) & (df['timestamp'] <= xmax)
		df = df[sel]
		# ymin = 50
		# ymax = 100
		# yticks = np.arange(ymin,ymax,10)
		pass
	elif xmax < 6.5*10**9:
		xmax = 6.5*10**9
		xminortick = MultipleLocator(1 * 10**8)
		xmajortick = MultipleLocator(0.5 * 10**9)
	elif xmax < 50*10**9:
		xmax = 50*10**9
		xminortick = MultipleLocator(1 * 10**9)
		xmajortick = MultipleLocator(5 * 10**9)
	else:
		print('WARING')
		# raise Exception()
	fig, ax = plt.subplots(figsize=figsize)
	for r in renderers:
		sel = sched_monitor_view.lang.filter.sel(df, r['filter'])
		X0 = df[r['x0']][sel]
		X1 = df[r['x1']][sel]
		Y0 = df[r['y0']][sel]
		Y1 = df[r['y1']][sel]
		N = len(X0)
		print('transpose starts')
		L = np.transpose(np.array([[X0,X1],[Y0,Y1]]))
		print('transpose ends')
		print('LineCollection starts')
		if 'line_width' not in r:
			r['line_width'] = None
		r['line_width'] = None
		lc = LineCollection(L,color=r['line_color'],linewidths=r['line_width'],label=r['label'])
		print('LineCollection ends')
		print('add_collection starts')
		ax.add_collection(lc)
		print('add_collection ends')
	ax.set_xlim(xmin, xmax)
	ax.set_ylim(ymin, ymax)
	ax.set_xlabel('Time in seconds')
	ax.set_ylabel('CPU')
	ax.set_yticks(yticks)
	if xmajortick is not None:
		ax.xaxis.set_major_locator(xmajortick)
	if xminortick is not None:
		ax.xaxis.set_minor_locator(xminortick)
	# ax.tick_params(which='minor', length=1)
	xticks = ax.get_xticks()
	def my_format(x):
		if x%10**9 == 0:
			return str(int(x/10**9))
		else:
			return str(x/10**9)
	ax.set_xticklabels([my_format(x) for x in xticks])
	print('savefig starts')
	name, ext = os.path.splitext(img)
	without_legend = name + ext
	fig.savefig(without_legend, bbox_inches='tight')
	ax.legend() #title='Frequency in GHz')
	handles, labels = ax.get_legend_handles_labels()
	with_legend = name + '_with_legend' + ext
	fig.savefig(with_legend, bbox_inches='tight')
	ncol=len(labels)
	fig = plt.figure(figsize=figsize) #(ncol*3,1))
	fig.legend(handles, labels, loc='center', frameon=False, ncol=ncol)
	legend_only = name + '_legend_only' + ext
	fig.savefig(legend_only, bbox_inches='tight')
	print('savefig ends')
	pass
