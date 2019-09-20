from smv.ViewController import ViewController
from bokeh.plotting import figure

class ScatterViewController(ViewController):
	"""docstring for ScatterViewController"""
	def __init__(self, *args, **kwargs):
		self.figure = figure(
			reset_policy="event_only",
			sizing_mode='stretch_both',
		)
		view = self.figure
		super(ScatterViewController, self).__init__(view, *args, **kwargs)
		