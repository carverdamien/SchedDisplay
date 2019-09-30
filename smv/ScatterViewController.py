from smv.ViewController import ViewController
from bokeh.plotting import figure
from bokeh.models.tools import HoverTool
from bokeh.layouts import column, row
from bokeh.models.widgets import Select, Button
from bokeh.models import ColumnDataSource
from bokeh.models.markers import X as Marker

class ScatterViewController(ViewController):
	"""docstring for ScatterViewController"""
	def __init__(self, *args, **kwargs):
		self.model = kwargs['model']
		self.columns_name = ['index'] + self.model.columns_name()
		self.source = kwargs.get('source', ColumnDataSource({}))
		self.select_yaxis = Select(
			options=self.columns_name,
		)
		self.select_xaxis = Select(
			options=self.columns_name,
		)
		self.button_plot = Button(
			label="Plot",
			button_type="success",
			width=100,
			width_policy="fixed",
			height=40,
			height_policy="fixed",
		)
		self.figure = figure(
			sizing_mode='stretch_both',
		)
		self.glyph = Marker()
		self.renderer = self.figure.add_glyph(self.source, self.glyph)
		tooltips = [("(x,y)","($x, $y)")]
		for k in self.columns_name:
			tooltips.append((k,"@"+str(k)))
		self.hovertool = HoverTool(tooltips=tooltips)
		self.figure.add_tools(self.hovertool)
		view = column(
			row(
				self.select_yaxis,
				self.select_xaxis,
				self.button_plot,
				sizing_mode='stretch_width',
			),
			self.figure,
			sizing_mode='stretch_both',
		)
		super(ScatterViewController, self).__init__(view, *args, **kwargs)
		self.button_plot.on_click(self.button_plot_on_click)

	def button_plot_on_click(self, event):
		self.source.data = ColumnDataSource.from_df(self.model.df)
		self.glyph.x=self.select_xaxis.value
		self.glyph.y=self.select_yaxis.value
