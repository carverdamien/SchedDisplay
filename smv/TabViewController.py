from bokeh.layouts import row, column
from bokeh.models.widgets import RadioButtonGroup

class TabViewController(object):
	"""docstring for TabViewController"""
	def __init__(self, labels, controllers, doc=None):
		super(TabViewController, self).__init__()
		self.labels = labels
		self.controllers = controllers
		self.views = [c.view for c in controllers]
		self.radiobuttongroup_tab = RadioButtonGroup(labels=labels)
		self.view = column(
			row(self.radiobuttongroup_tab, sizing_mode='scale_width',),
			row(*self.views, sizing_mode = 'stretch_both')
		)
		self.doc = doc
