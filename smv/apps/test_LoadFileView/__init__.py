from smv.LoadFileViewController import LoadFileViewController

def modify_doc(doc):
	ctrl = LoadFileViewController('.','.py',doc=doc)
	doc.add_root(ctrl.view)
