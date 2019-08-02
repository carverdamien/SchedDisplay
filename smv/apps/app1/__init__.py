from smv.TabView import TabView
from smv.ConsoleView import ConsoleView

def modify_doc(doc):
	console = [ConsoleView(doc=doc), ConsoleView(doc=doc)]
	labels = ['Console 0', 'Console 1']
	views = [console[0].view, console[1].view]
	tab = TabView(labels, views, doc=doc)
	doc.add_root(tab.view)
	pass
