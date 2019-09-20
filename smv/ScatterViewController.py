from smv.ViewController import ViewController
from bokeh.plotting import figure
from bokeh.layouts import column, row
from bokeh.models.widgets import Select, Button
from bokeh.models import ColumnDataSource
from bokeh.models.markers import X as Marker

class ScatterViewController(ViewController):
	"""docstring for ScatterViewController"""
	def __init__(self, *args, **kwargs):
		self.model = kwargs['model']
		self.source = kwargs.get('source', ColumnDataSource({}))
		self.select_yaxis = Select(
			options=self.model.columns_name(),
		)
		self.select_xaxis = Select(
			options=self.model.columns_name(),
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
			reset_policy="event_only",
			sizing_mode='stretch_both',
		)
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
		self.figure.renderers.clear()
		self.source.data = ColumnDataSource.from_df(self.model.df)
		glyph = Marker(
			x=self.select_xaxis.value,
			y=self.select_yaxis.value,
		)
		renderer = self.figure.add_glyph(self.source, glyph)