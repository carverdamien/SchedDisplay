from bokeh.models.widgets import DataTable
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TableColumn
import os
import pandas as pd

def modify_doc(doc):
	fname = sorted(list(find_files('examples/trace','.tar')))
	dd = {'fname':fname}
	df = pd.DataFrame(dd)
	columns = [TableColumn(field=c, title=c) for c in df.columns]
	source = ColumnDataSource(df)
	table = DataTable(
		source=source,
		columns=columns,
		sizing_mode='stretch_both',
		width_policy='max',
		selectable=True,
	)

	doc.add_root(table)
	pass

def find_files(directory, ext):
	for root, dirs, files in os.walk(directory, topdown=False):
		for name in files:
			path = os.path.join(root, name)
			if ext == os.path.splitext(name)[1]:
				yield path