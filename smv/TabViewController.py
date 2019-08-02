from bokeh.layouts import row, column
from bokeh.models.widgets import RadioButtonGroup

class TabViewController(object):
	"""docstring for TabViewController"""
	def __init__(self, labels, controllers, doc=None):
		super(TabViewController, self).__init__()
		self.labels = labels
		self.controllers = controllers
		self.views = [c.view for c in controllers]
		for v in self.views:
			v.visible = False
		self.radiobuttongroup_tab = RadioButtonGroup(labels=labels)
		self.radiobuttongroup_tab.on_click(self.on_click_radiobuttongroup_tab)
		self.view = column(
			row(self.radiobuttongroup_tab, sizing_mode='scale_width',),
			row(*self.views, sizing_mode = 'stretch_both')
		)
		self.doc = doc

	def on_click_radiobuttongroup_tab(self, new):
		for c in self.controllers:
			c.hide()
		selected = self.controllers[self.radiobuttongroup_tab.active]
		selected.show()
		pass
