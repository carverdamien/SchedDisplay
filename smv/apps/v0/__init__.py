from smv.TabViewController import TabViewController
from smv.ConsoleViewController import ConsoleViewController
from smv.LoadFileViewController import LoadFileViewController
from smv.FigureViewController import FigureViewController
from smv.SeqViewController import SeqViewController
import json

import pandas as pd
import numpy as np

def dummy_lines():
	px_height = 4
	y0_shift = 0. / float(px_height)
	y1_shift = 2. / float(px_height)
	N = 10000000
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
		'category':c,
	})
	df['category'] = df['category'].astype('category')
	# df.sort_values(by='x0', inplace=True)
	# df.index = np.arange(len(df))
	return df

def modify_doc(doc):
	nr_cpu = 160
	px_height = 4
	height = (nr_cpu+2)*px_height
	width = 1080 # May want to make width custumizable?
	console = ConsoleViewController(doc=doc)
	log = console.write
	load_trace = LoadFileViewController('./examples/trace','.hdf5',doc=doc, log=log)
	load_plot = LoadFileViewController('./examples/plot','.json',doc=doc, log=log)
	figure = FigureViewController(doc=doc, log=log)
	seq = SeqViewController([load_trace, load_plot, figure], doc=doc, log=log)
	labels = ['Main','Server Console']
	tab = TabViewController(labels, [seq, console], doc=doc, log=log)
	def on_loaded_trace(io):
		trace = io.read()
		console.write('Trace: {} bytes loaded'.format(len(trace)))
		seq.next()
	load_trace.on_loaded(on_loaded_trace)
	def on_loaded_plot(io):
		plot = io.read()
		console.write('Plot:{}'.format(plot))
		try:
			plot = json.loads(plot)
		except Exception as e:
			console.write(e)
			return
		seq.next()
		figure.plot(dummy_lines(), width, height)
	load_plot.on_loaded(on_loaded_plot)
	doc.add_root(tab.view)
	seq.next()
	pass
