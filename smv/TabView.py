from bokeh.layouts import row, column
from bokeh.models.widgets import RadioButtonGroup

class TabView(object):
	"""docstring for TabView"""
	def __init__(self, labels, views, doc=None):
		super(TabView, self).__init__()
		self.radiobuttongroup_tab = RadioButtonGroup(labels=labels)
		self.view = column(
			row(self.radiobuttongroup_tab, sizing_mode='scale_width',),
			row(*views, sizing_mode = 'stretch_both')
		)
		self.doc = doc
