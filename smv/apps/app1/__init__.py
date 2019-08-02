from smv.TabViewController import TabViewController
from smv.ConsoleViewController import ConsoleViewController
from threading import Thread

def modify_doc(doc):
	labels = ['Console 0', 'Console 1']
	console = [ConsoleViewController(doc=doc), ConsoleViewController(doc=doc)]
	tab = TabViewController(labels, console, doc=doc)
	doc.add_root(tab.view)
	def target():
		from time import sleep
		i=0
		while True:
			console[0].write(i)
			sleep(1)
			i+=2
	t=Thread(target=target)
	t.daemon = True
	t.start()
	def target():
		from time import sleep
		i=1
		while True:
			console[1].write(i)
			sleep(1)
			i+=2
	t=Thread(target=target)
	t.daemon = True
	t.start()
	pass
