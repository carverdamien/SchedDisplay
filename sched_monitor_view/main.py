from bokeh.layouts import row, column
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource
from DataSelector import DataSelector

plot = figure(x_range=(0, 100), y_range=(0, 100), toolbar_location=None)
source = ColumnDataSource(data=dict(x=[], y=[]))
plot.line(
    'x',
    'y',
    source=source,
    line_width=3,
)
doc = curdoc()
root = column(plot, DataSelector(doc))
doc.add_root(root)
