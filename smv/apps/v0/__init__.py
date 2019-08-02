from smv.TabViewController import TabViewController
from smv.ConsoleViewController import ConsoleViewController
from smv.LoadFileViewController import LoadFileViewController
from smv.FigureViewController import FigureViewController
from smv.SeqViewController import SeqViewController
import json

def modify_doc(doc):
	console = ConsoleViewController(doc=doc)
	log = console.write
	load_trace = LoadFileViewController('./examples/trace','.hdf5',doc=doc, log=log)
	load_plot = LoadFileViewController('./examples/plot','.json',doc=doc, log=log)
	figure = FigureViewController(doc=doc)
	seq = SeqViewController([load_trace, load_plot, figure], doc=doc, log=log)
	labels = ['Main','Console']
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
			seq.next()
		except Exception as e:
			console.write(e)
	load_plot.on_loaded(on_loaded_plot)
	doc.add_root(tab.view)
	seq.next()
	pass
