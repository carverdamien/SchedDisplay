from bokeh.plotting import curdoc
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TableColumn
from tornado import gen
from functools import partial
import json
import pandas as pd
import bg.loadDataFrame
doc = curdoc()
STATE = {
	'hdf5' : [],
}
DF = {}
def from_json(new_state, done):
	new_state = json.loads(new_state)
	STATE.clear()
	DF.clear()
	load_many_hdf5(STATE['hdf5'], done)
def to_json():
	return json.dumps(STATE)
def is_valid(new_state):
	try:
		return not to_json() == json.dumps(json.loads(new_state))
	except json.decoder.JSONDecodeError as e:
		pass
	return False
def hdf5_is_loaded(path):
	return path in STATE['hdf5']
@gen.coroutine
def coroutine_load_hdf5(path, df, done):
	DF[path] = df
	STATE['hdf5'].append(path)
	done()
def callback_load_hdf5(path, df, done):
    doc.add_next_tick_callback(partial(coroutine_load_hdf5, path, df, done))
def load_hdf5(path, done):
	bg.loadDataFrame.bg(path, callback_load_hdf5, done).start()
def load_many_hdf5(paths, done):
	if len(paths) == 0:
		done()
	else:
		def my_done():
			load_many_hdf5(paths[1:], done)
		load_hdf5(paths[0], my_done)
def unload_hdf5(path):
	del DF[path]
	STATE['hdf5'].remove(path)
def update_source(src):
	# src.data = ColumnDataSource.from_df(DF[0])
	pass
def update_table(table):
	# table.columns = [TableColumn(field=c, title=c) for c in DF[0].columns]
	pass
