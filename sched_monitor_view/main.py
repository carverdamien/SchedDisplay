# External imports
from bokeh.layouts import row, column
from bokeh.plotting import curdoc, figure
from bokeh.models.widgets import Select, CheckboxGroup, Button
from bokeh.models import ColumnDataSource
from tornado import gen
from functools import partial
# Internal imports
import Types
import feeds.fspath
import bg.loadData
import bg.updateSource

# Build the components
doc = curdoc()
checkboxgroup_event = CheckboxGroup(
    labels = Types.EVENT
)
checkboxgroup_interval = CheckboxGroup(
    labels = Types.INTERVAL
)
select_hdf5 = Select(
    title ='Data:'
)
button_load_hdf5 = Button(
    label="load",
    button_type="success",
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
    for i in range(len(Types.EVENT))
]
source_interval = [
    ColumnDataSource(
        data=dict(x0=[], y0=[], x1=[], y1=[])
    )
    for i in range(len(Types.INTERVAL))
]
segment_event = [
    figure_plot.segment(
        'x0',
        'y0',
        'x1',
        'y1',
        source=source_event[i],
    )
    for i in range(len(source_event))
]
segment_interval = [
    figure_plot.segment(
        'x0',
        'y0',
        'x1',
        'y1',
        source=source_event[i],
    )
    for i in range(len(source_interval))
]
button_plot = Button(
    label="Plot",
    button_type="success",
    disabled=True,
)

# Add feeds
root = './raw/hackbench/monitored'
ext  = '.hdf5'
@gen.coroutine
def coroutine_fspath(l):
    select_hdf5.options = l
    select_hdf5.value = l[0]
def callback_fspath(l):
    doc.add_next_tick_callback(partial(coroutine_fspath, l))
feeds.fspath.feed(root,ext,callback_fspath).start()

# Add interactivity
data = {}
@gen.coroutine
def coroutine_loadData(path, new_data):
    data.clear()
    data.update(new_data)
    button_load_hdf5.disabled = False
    button_plot.disabled = False
    select_hdf5.title = "Data: {}".format(path)
def callback_loadData(path, new_data):
    doc.add_next_tick_callback(partial(coroutine_loadData, path, new_data))
def on_click_loadhdf5(new):
    button_load_hdf5.disabled = True
    button_plot.disabled = True
    path = select_hdf5.value
    bg.loadData.load(path, callback_loadData).start()
button_load_hdf5.on_click(on_click_loadhdf5)
@gen.coroutine
def coroutine_plot(source_event_data, source_interval_data):
    for i in range(len(source_event)):
        source_event[i].data = source_event_data[i]
    for i in range(len(source_interval)):
        source_interval[i].data = source_interval_data[i]
    button_load_hdf5.disabled = False
    button_plot.disabled = False
    pass
def callback_plot(source_event_data, source_interval_data):
    doc.add_next_tick_callback(
        partial(
            coroutine_plot,
            source_event_data,
            source_interval_data,
        )
    )
def on_click_plot(new):
    button_load_hdf5.disabled = True
    button_plot.disabled = True
    event = checkboxgroup_event.active
    interval = checkboxgroup_interval.active
    bg.updateSource.plot(data, event, interval, callback_plot).start()
button_plot.on_click(on_click_plot)
# assamble components
root = column(
    figure_plot,
    select_hdf5,
    button_load_hdf5,
    row(checkboxgroup_event, checkboxgroup_interval),
    button_plot,
)
doc.add_root(root)
