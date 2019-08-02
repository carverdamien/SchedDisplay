from smv.ConsoleView import ConsoleView
from threading import Thread

def modify_doc(doc):
	console = ConsoleView()
	def target():
		from time import sleep
		i=0
		while True:
			sleep(.01)
			console.write(i)
			i+=1
	t=Thread(target=target)
	t.daemon = True
	t.start()
	doc.add_root(console.view)
	console.doc = doc
	pass
