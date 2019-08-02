from smv.TabViewController import TabViewController
from smv.ConsoleViewController import ConsoleViewController
from smv.LoadFileViewController import LoadFileViewController
from smv.FigureViewController import FigureViewController
from smv.SeqViewController import SeqViewController

def modify_doc(doc):
	console = ConsoleViewController(doc=doc)
	load = LoadFileViewController('.','.py',doc=doc)
	figure = FigureViewController(doc=doc)
	seq = SeqViewController([load, figure], doc=doc)
	labels = ['Main','Console']
	tab = TabViewController(labels, [seq, console], doc=doc)
	def on_loaded(io):
		console.write('{} bytes loaded'.format(len(io.read())))
		seq.next()
	load.on_loaded(on_loaded)
	doc.add_root(tab.view)
	seq.next()
	pass
