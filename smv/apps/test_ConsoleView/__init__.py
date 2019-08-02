from smv.ConsoleViewController import ConsoleViewController
from threading import Thread

def modify_doc(doc):
	console = ConsoleViewController()
	def target():
		from time import sleep
		i=0
		while True:
			console.write(i)
			sleep(1)
			console.hide()
			sleep(1)
			console.show()
			i+=1
	t=Thread(target=target)
	t.daemon = True
	t.start()
	doc.add_root(console.view)
	console.doc = doc
	pass
