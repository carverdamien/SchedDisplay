from smv.TabViewController import TabViewController
from smv.ConsoleViewController import ConsoleViewController
from smv.SelectFileViewController import SelectFileViewController
from smv.FigureViewController import FigureViewController
from smv.SeqViewController import SeqViewController

def modify_doc(doc):
	console = ConsoleViewController(doc=doc)
	select = SelectFileViewController('.','.py',doc=doc)
	figure = FigureViewController(doc=doc)
	seq = SeqViewController([select, figure], doc=doc)
	labels = ['Main','Console']
	tab = TabViewController(labels, [seq, console], doc=doc)
	doc.add_root(tab.view)
	seq.next()
	pass
