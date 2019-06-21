from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TableColumn
import json
import pandas as pd
STATE = {
	'hdf5' : [],
}
DF = pd.DataFrame()
def from_json(new_state):
	new_state = json.loads(new_state)
	STATE.clear()
	STATE.update(new_state)
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
def load_hdf5(path):
	# TODO
	STATE['hdf5'].append(path)
def unload_hdf5(path):
	# TODO
	STATE['hdf5'].remove(path)
def update_source(src):
	src.data = ColumnDataSource.from_df(DF)
def update_table(table):
	table.columns = [TableColumn(field=c, title=c) for c in DF.columns]
