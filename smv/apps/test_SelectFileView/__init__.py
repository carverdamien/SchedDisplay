from smv.SelectFileViewController import SelectFileViewController

def modify_doc(doc):
	ctrl = SelectFileViewController('.','.py',doc=doc)
	doc.add_root(ctrl.view)
