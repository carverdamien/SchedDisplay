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
	def select_on_click(new):
		seq.next()
	select.button.on_click(select_on_click)
	doc.add_root(tab.view)
	seq.next()
	pass
