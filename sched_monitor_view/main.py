# External imports
from bokeh.layouts import row, column
from bokeh.plotting import curdoc, figure
from bokeh.models.glyphs import Segment
from bokeh.models import Legend, LegendItem
from bokeh.models.widgets import Select, CheckboxGroup, Button, Dropdown, ColorPicker, RangeSlider, Slider, TextAreaInput, RadioButtonGroup, DataTable, TableColumn
from bokeh.models import ColumnDataSource
from tornado import gen
from functools import partial
# Internal imports
import feeds.fspath
import state

######################################################
################ Build the components ################
######################################################
doc = curdoc()
################ TABS View ################
radiobuttongroup_tab = RadioButtonGroup(
	labels=["User View", "JSON View", "Data View", "Plot View"],
)
################ User View ################
select_hdf5 = Select(
    title ='Path:',
    sizing_mode="fixed",
    visible=False,
)
button_add_or_rm_hdf5 = Button(
    align="end",
    button_type="success",
    width_policy="min",
    visible=False,
)
USER_VIEW = [select_hdf5,button_add_or_rm_hdf5]
################ JSON View ################
textareainput_json = TextAreaInput(visible=False)
button_import_json = Button(
	label="Import",
	align="end",
    button_type="success",
    width_policy="min",
    visible=False,
)
JSON_VIEW = [textareainput_json, button_import_json]
################ Data View ################
source_datatable = ColumnDataSource({'empty_data':[]})
columns_datatable = [ TableColumn(field="empty_data", title="empty data") ]
datatable = DataTable(source=source_datatable, columns=columns_datatable, visible=False)
DATA_VIEW = [datatable]
################ Plot View ################
figure_plot = figure(
    sizing_mode='stretch_both',
    tools="xpan,reset,save,xwheel_zoom,hover",
    active_scroll='xwheel_zoom',
    output_backend="webgl",
    visible=False,
)
PLOT_VIEW = [figure_plot]
################ All Views ################
VIEWS = [
	USER_VIEW,
	JSON_VIEW,
	DATA_VIEW,
	PLOT_VIEW,
]
###########################################
################ Add feeds ################
###########################################
@gen.coroutine
def coroutine_fspath(l):
    select_hdf5.options = l
    select_hdf5.value = l[0]
def callback_fspath(l):
    doc.add_next_tick_callback(partial(coroutine_fspath, l))
feeds.fspath.feed('./raw', '.hdf5',callback_fspath).start()
###################################################
################ Add interactivity ################
###################################################
################ TABS View ################
def on_click_radiobuttongroup_tab(new):
	selected = radiobuttongroup_tab.active
	for i in range(len(VIEWS)):
		for e in VIEWS[i]:
			if i == selected:
				e.visible = True
			else:
				e.visible = False
	pass
radiobuttongroup_tab.on_click(on_click_radiobuttongroup_tab)
################ User View ################
def label_button_add_or_rm_hdf5():
	path = select_hdf5.value
	if state.hdf5_is_loaded(path):
		button_add_or_rm_hdf5.label = 'rm'
		button_add_or_rm_hdf5.button_type = 'warning'
	else:
		button_add_or_rm_hdf5.label = 'add'
		button_add_or_rm_hdf5.button_type = 'success'
def on_change_select_hdf5(attr, old, new):
    label_button_add_or_rm_hdf5()
select_hdf5.on_change('value', on_change_select_hdf5)
def on_click_loadhdf5(new):
	path = select_hdf5.value
	if state.hdf5_is_loaded(path):
		state.unload_hdf5(path)
	else:
		state.load_hdf5(path)
	label_button_add_or_rm_hdf5()
button_add_or_rm_hdf5.on_click(on_click_loadhdf5)
#####################################################
################ Assamble components ################
#####################################################
root = column(
    row(
        radiobuttongroup_tab,
        sizing_mode = 'scale_width',
    ),
    row(
		select_hdf5,
		button_add_or_rm_hdf5,
		button_import_json,
		sizing_mode = 'scale_width',
    ),
    textareainput_json,
    datatable,
    figure_plot,
    sizing_mode = 'stretch_both',
)
doc.add_root(root)
