from bokeh.layouts import row, column
from bokeh.plotting import curdoc, figure
from bokeh.models.widgets import Select, CheckboxGroup
from bokeh.models import ColumnDataSource

import EventTypes

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
root = column(figure_plot, select_hdf5, checkboxgroup_event)
doc.add_root(root)
