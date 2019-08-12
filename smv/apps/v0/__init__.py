from smv.TabViewController import TabViewController
from smv.ConsoleViewController import ConsoleViewController, logFunctionCall
from smv.LoadFileViewController import LoadFileViewController
from smv.FigureViewController import FigureViewController
from smv.SeqViewController import SeqViewController
from smv.DataFrame import DataFrame
import json
import pandas as pd

def modify_doc(doc):
	nr_cpu = 160
	px_height = 4
	height = (nr_cpu+2)*px_height
	width = 1080 # May want to make width custumizable?
	state = {
		'nr_cpu' : nr_cpu,
		'px_height' : px_height,
		'height' : height,
		'width' : width,
		'y0_shift' : 0. / float(px_height),
		'y1_shift' : 2. / float(px_height),
	}
	console = ConsoleViewController(doc=doc)
	log = console.write
	@logFunctionCall(log)
	def lines_from_df(df):
		lines = pd.DataFrame({
			'x0':df['timestamp'],
			'x1':df['timestamp'],
			'y0':df['cpu']+state['y0_shift'],
			'y1':df['cpu']+state['y1_shift'],
			'category':df['event'],
		})
		lines['category'] = lines['category'].astype('category')
		return lines
	load_trace = LoadFileViewController('./examples/trace','.hdf5',doc=doc, log=log)
	load_plot = LoadFileViewController('./examples/plot','.json',doc=doc, log=log)
	figure = FigureViewController(doc=doc, log=log)
	seq = SeqViewController([load_trace, load_plot, figure], doc=doc, log=log)
	labels = ['Main','Server Console']
	tab = TabViewController(labels, [seq, console], doc=doc, log=log)
	@logFunctionCall(log)
	def on_loaded_trace(io):
		df = DataFrame(io)
		console.write('{} records in trace'.format(len(df)))
		state['df'] = df
		state['lines'] = lines_from_df(df)
		seq.next()
	load_trace.on_loaded(on_loaded_trace)
	@logFunctionCall(log)
	def on_loaded_plot(io):
		plot = io.read()
		console.write('Plot:{}'.format(plot))
		try:
			plot = json.loads(plot)
		except Exception as e:
			console.write(e)
			return
		seq.next()
		figure.plot(state['width'], state['height'], state['lines'])
	load_plot.on_loaded(on_loaded_plot)
	doc.add_root(tab.view)
	seq.next()
	pass
