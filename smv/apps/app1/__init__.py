from smv.TabViewController import TabViewController
from smv.ConsoleViewController import ConsoleViewController

def modify_doc(doc):
	labels = ['Console 0', 'Console 1']
	console = [ConsoleViewController(doc=doc), ConsoleViewController(doc=doc)]
	tab = TabViewController(labels, console, doc=doc)
	doc.add_root(tab.view)
	pass
