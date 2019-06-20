# External imports
from bokeh.layouts import row, column
from bokeh.plotting import curdoc, figure
from bokeh.models.glyphs import Segment
from bokeh.models import Legend, LegendItem
from bokeh.models.widgets import Select, CheckboxGroup, Button, Dropdown, ColorPicker, RangeSlider, Slider
from bokeh.models import ColumnDataSource
from tornado import gen
from functools import partial
# Internal imports
import Types
import feeds.fspath
import bg.loadData
import bg.updateSource

TYPES = Types.EVENT+Types.INTERVAL
data = {}
color = {
    k:'#FFFFFF'
    for k in TYPES
}
# Build the components
doc = curdoc()
select_hdf5 = Select(
    title ='Path:',
    sizing_mode="fixed",
)
button_load_hdf5 = Button(
    label="Load",
    align="end",
    button_type="success",
    width_policy="min",
)
select_types = Select(
    title="Types",
    sizing_mode="fixed",
    options=TYPES,
    value=TYPES[0],
)
colorpicker_types = ColorPicker(
    width=50,
    sizing_mode="fixed",
    align='end',
    color='#FFFFFF',
)
rangeslider_t0 = RangeSlider(
    start=0,
    end=100,
    value=(0,100),
    step=1,
    sizing_mode="scale_width",
    disabled=True,
    callback_policy="mouseup",
)
rangeslider_t0_value = [0,100]
slider_truncate = Slider(
    title='Truncate (<=1000 Recommended)',
    start=2,
    end=1000,
    value=1000,
    width=300,
    sizing_mode="fixed",
)
button_plot = Button(
    align='end',
    label="Plot",
    button_type="success",
    width_policy="min",
    disabled=True,
)
TOOLTIPS = [
    ("type","@t"),
    ("timestamp","@x0"),
    ("pid","@pid"),
    ("addr","@addr"),
    ("arg0","@arg0"),
    ("arg1","@arg1"),
]
figure_plot = figure(
    sizing_mode='stretch_both',
    tools="xpan,reset,save,xwheel_zoom,hover",
    tooltips=TOOLTIPS,
    active_scroll='xwheel_zoom',
    output_backend="webgl",
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
items=[]
index=0
segment_event = [
    Segment(
        x0='x0',
        x1='x1',
        y0='y0',
        y1='y1',
        line_color='#FFFFFF',
    )
    for i in range(len(source_event))
]

for i in range(len(source_event)):
    r = figure_plot.add_glyph(source_event[i], segment_event[i])
    items.append(LegendItem(label=Types.EVENT[i], renderers=[r], index=index))
    index+=1
segment_interval = [
    Segment(
        x0='x0',
        x1='x1',
        y0='y0',
        y1='y1',
        line_color='#FFFFFF'
    )
    for i in range(len(source_interval))
]
for i in range(len(source_interval)):
    r = figure_plot.add_glyph(source_interval[i], segment_interval[i])
    items.append(LegendItem(label=Types.INTERVAL[i], renderers=[r], index=index))
    index+=1
legend = Legend(items=items)
figure_plot.add_layout(legend)
# Add feeds
root = './raw'
ext  = '.hdf5'
@gen.coroutine
def coroutine_fspath(l):
    select_hdf5.options = l
    select_hdf5.value = l[0]
def callback_fspath(l):
    doc.add_next_tick_callback(partial(coroutine_fspath, l))
feeds.fspath.feed(root,ext,callback_fspath).start()

# Add interactivity
def on_change_select_hdf5(attr, old, new):
    path = select_hdf5.value
    if path in data:
        button_load_hdf5.label = 'rm'
        button_load_hdf5.button_type = 'warning'
    else:
        button_load_hdf5.label = 'add'
        button_load_hdf5.button_type = 'success'
    pass
select_hdf5.on_change('value', on_change_select_hdf5)
def on_change_select_types(attr, old, new):
    type_selected = select_types.value
    colorpicker_types.color = color[type_selected]
select_types.on_change('value', on_change_select_types)
def on_change_colorpicker_types(attr, old, new):
    type_selected = select_types.value
    new_color = colorpicker_types.color
    if type_selected in Types.EVENT:
        i = Types.ID_EVENT[type_selected]
        segment_event[i].line_color = new_color
    elif type_selected in Types.INTERVAL:
        i = Types.ID_INTERVAL[type_selected]
        segment_interval[i].line_color = new_color
    else:
        raise Exception()
    color[type_selected] = new_color
    pass
colorpicker_types.on_change('color', on_change_colorpicker_types)
@gen.coroutine
def coroutine_loadData(path, new_data):
    if path in data:
        raise Exception()
    data[path]=new_data
    rangeslider_t0.end = max([data[path][cpu]['timestamp'][-1] for path in data for cpu in data[path]])
    rangeslider_t0.value = (rangeslider_t0.start, rangeslider_t0.end)
    rangeslider_t0_value[0] = rangeslider_t0.start
    rangeslider_t0_value[1] = rangeslider_t0.end
    figure_plot.x_range.start = rangeslider_t0.start
    figure_plot.x_range.end = rangeslider_t0.end
    figure_plot.y_range.start = 0
    figure_plot.y_range.end = sum([1 for path in data for cpu in data[path]])
    slider_truncate.value = 1000
    slider_truncate.end = max([len(data[path][cpu]['timestamp']) for path in data for cpu in data[path]])
    button_load_hdf5.label = 'rm'
    button_load_hdf5.button_type = 'warning'
    button_load_hdf5.disabled = False
    button_plot.disabled = False
    rangeslider_t0.disabled = False
def callback_loadData(path, new_data):
    doc.add_next_tick_callback(partial(coroutine_loadData, path, new_data))
def on_click_loadhdf5(new):
    path = select_hdf5.value
    if path in data:
        del data[path]
        button_load_hdf5.label = 'add'
        button_load_hdf5.button_type = 'success'
        if len(data) == 0:
            button_plot.disabled = True
            rangeslider_t0.disabled = True
        else:
            rangeslider_t0.end = max([data[path][cpu]['timestamp'][-1] for path in data for cpu in data[path]])
            rangeslider_t0.value = (rangeslider_t0.start, rangeslider_t0.end)
            rangeslider_t0_value[0] = rangeslider_t0.start
            rangeslider_t0_value[1] = rangeslider_t0.end
    else:
        button_load_hdf5.disabled = True
        button_plot.disabled = True
        rangeslider_t0.disabled = True
        bg.loadData.load(path, callback_loadData).start()
button_load_hdf5.on_click(on_click_loadhdf5)
@gen.coroutine
def coroutine_plot(source_event_data, source_interval_data, tlim):
    rangeslider_t0.value = tlim
    rangeslider_t0_value[0] = tlim[0]
    rangeslider_t0_value[1] = tlim[1]
    figure_plot.x_range.start = tlim[0]
    figure_plot.x_range.end = tlim[1]
    for i in range(len(source_event)):
        source_event[i].data = source_event_data[i]
    for i in range(len(source_interval)):
        source_interval[i].data = source_interval_data[i]
    button_load_hdf5.disabled = False
    button_plot.disabled = False
    rangeslider_t0.disabled = False
    pass
def callback_plot(source_event_data, source_interval_data, tlim):
    doc.add_next_tick_callback(
        partial(
            coroutine_plot,
            source_event_data,
            source_interval_data,
            tlim,
        )
    )
def go_plot(tlim):
    button_load_hdf5.disabled = True
    button_plot.disabled = True
    rangeslider_t0.disabled = True
    truncate = slider_truncate.value
    event    = [i for i in range(len(Types.EVENT))    if color[Types.EVENT[i]]    != '#FFFFFF']
    interval = [i for i in range(len(Types.INTERVAL)) if color[Types.INTERVAL[i]] != '#FFFFFF']
    bg.updateSource.plot(data, truncate, event, interval, tlim, callback_plot).start()
def on_click_plot(new):
    tlim = rangeslider_t0.value
    go_plot(tlim)
button_plot.on_click(on_click_plot)
def on_change_rangeslider_t0(attr, old, new):
    value = tuple(new)
    if rangeslider_t0_value is not None and new[1] > rangeslider_t0_value[1]:
        value = (new[0]+new[1]-rangeslider_t0_value[1], new[1])
    go_plot(value)
rangeslider_t0.on_change('value_throttled', on_change_rangeslider_t0)
# assamble components
root = column(
    row(
        select_hdf5,
        button_load_hdf5,
        select_types,
        colorpicker_types,
        slider_truncate,
        button_plot,
        sizing_mode = 'scale_width',
    ),
    figure_plot,
    rangeslider_t0,
    sizing_mode = 'stretch_both',
)
doc.add_root(root)
