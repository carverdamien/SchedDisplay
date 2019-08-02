from smv.ViewController import ViewController
from bokeh.models.widgets import Select

class SelectFileViewController(ViewController):
	"""docstring for SelectFileViewController"""
	def __init__(self, doc=None):
		options=["foo", "bar", "baz", "quux"] # TODO
		view = Select(
			title="Select File:",
			value=options[0],
			options=options,
		)
		super(SelectFileViewController, self).__init__(view, doc)
