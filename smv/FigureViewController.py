from smv.ViewController import ViewController
from bokeh.plotting import figure

class FigureViewController(ViewController):
	"""docstring for FigureViewController"""
	def __init__(self, doc=None, log=None):
		view = figure()
		super(FigureViewController, self).__init__(view, doc, log)
