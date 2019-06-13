from bokeh.layouts import row, column
from bokeh.plotting import curdoc, figure
from DataSelector import DataSelector
from Source import Source

from bokeh.models.widgets import CheckboxGroup
import EventTypes

m = CheckboxGroup(
    labels = EventTypes.EVENT
)

doc = curdoc()

select = DataSelector(doc)
plot = figure(
    plot_height=540,
    plot_width=960,
    sizing_mode='scale_width',
    tools="xpan,reset,save,xwheel_zoom",
    active_scroll='xwheel_zoom',
)
source = Source(doc, select, plot)
for i in range(len(source)):
    plot.segment(
        'x0',
        'y0',
        'x1',
        'y1',
        source=source[i],
        legend=str(i),
    )
plot.legend.click_policy="hide"
root = column(plot, select, m)
doc.add_root(root)
