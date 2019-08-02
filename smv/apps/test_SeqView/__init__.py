from smv.SeqViewController import SeqViewController
from smv.ViewController import ViewController
from bokeh.models.widgets import Button

def modify_doc(doc):
	N = 10
	button = [Button(label="Button {}".format(i)) for i in range(N)]
	controller = [ViewController(view=button[i], doc=doc) for i in range(N)]
	seq = SeqViewController(controller, doc=doc)
	for i in range(N):
		def on_click(new):
			seq.next()
		button[i].on_click(on_click)
	doc.add_root(seq.view)
	seq.next()
