from smv.SelectFileViewController import SelectFileViewController

def modify_doc(doc):
	ctrl = SelectFileViewController(doc=doc)
	doc.add_root(ctrl.view)
