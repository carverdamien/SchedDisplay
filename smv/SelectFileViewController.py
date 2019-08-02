from smv.ViewController import ViewController
from bokeh.models.widgets import Select
import os

def find_files(directory, ext):
	for root, dirs, files in os.walk(directory, topdown=False):
		for name in files:
			path = os.path.join(root, name)
			if ext == os.path.splitext(name)[1]:
				yield path

class SelectFileViewController(ViewController):
	"""docstring for SelectFileViewController"""
	def __init__(self, directory, ext, doc=None):
		options=sorted(list(find_files(directory,ext)))
		view = Select(
			title="Select File:",
			value=options[0],
			options=options,
			height=40,
			height_policy="fixed",
		)
		super(SelectFileViewController, self).__init__(view, doc)
