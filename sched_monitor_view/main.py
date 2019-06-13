# External imports
from bokeh.layouts import row, column
from bokeh.plotting import curdoc, figure
from bokeh.models.widgets import Select, CheckboxGroup, Button
from bokeh.models import ColumnDataSource
from tornado import gen
from functools import partial
# Internal imports
import EventTypes
import feeds.fspath

# Build the components
doc = curdoc()
checkboxgroup_event = CheckboxGroup(
    labels = EventTypes.EVENT
)
select_hdf5 = Select(
    title ='Data:'
)
figure_plot = figure(
    plot_height=540,
    plot_width=960,
    sizing_mode='scale_width',
    tools="xpan,reset,save,xwheel_zoom",
    active_scroll='xwheel_zoom',
)
source_event = [
    ColumnDataSource(
        data=dict(x0=[], y0=[], x1=[], y1=[])
    )
    for i in range(len(EventTypes.EVENT))
]
for i in range(len(source_event)):
    figure_plot.segment(
        'x0',
        'y0',
        'x1',
        'y1',
        source=source_event[i],
    )
button_plot = Button(
    label="Plot",
    button_type="success",
)
root = column(figure_plot, select_hdf5, checkboxgroup_event, button_plot)
doc.add_root(root)

# Add feeds
root = './raw/hackbench/monitored'
ext  = '.hdf5'
@gen.coroutine
def coroutine(l):
    select_hdf5.options = l
def callback(l):
    doc.add_next_tick_callback(partial(coroutine, l))
feeds.fspath.feed(root,ext,callback).start()

# Add interactivity
