from bokeh.layouts import row, column
from bokeh.models.widgets import RadioButtonGroup
from smv.ViewController import ViewController

class TabViewController(ViewController):
	"""docstring for TabViewController"""
	def __init__(self, labels, controllers, doc=None):
		radiobuttongroup_tab = RadioButtonGroup(labels=labels)
		views = [c.view for c in controllers]
		view = column(
			row(radiobuttongroup_tab, sizing_mode='scale_width',),
			row(*views, sizing_mode = 'stretch_both')
		)
		super(TabViewController, self).__init__(view, doc)
		self.labels = labels
		self.controllers = controllers
		self.views = views
		for v in self.views:
			v.visible = False
		self.radiobuttongroup_tab = radiobuttongroup_tab
		self.radiobuttongroup_tab.on_click(self.on_click_radiobuttongroup_tab)

	def on_click_radiobuttongroup_tab(self, new):
		for c in self.controllers:
			c.hide()
		selected = self.controllers[self.radiobuttongroup_tab.active]
		selected.show()
		pass
