from smv.TableModel import TracesModel, Column, parsable_column
from smv.TableViewController import TableViewController
from bokeh.models import Panel, Tabs

def modify_doc(doc):
	model = TracesModel()
	def fname(i):
		return i
	model.add_column(Column(dtype=str, function=fname))
	COLUMNS = [
		[float, 'usr_bin_time',  'time.err', '{pattern:F}'],
		[float, 'sysbench_trps', 'run.out',  '{:s}transactions:{:s}{:d}{:s}({pattern:F} per sec.)'],
	]
	for i in range(4):
		COLUMNS.extend([
			[float, 'cpu%d_package_joules'%(i), 'cpu-energy-meter.out',  'cpu%d_package_joules={pattern:F}'%(i)],
			[float, 'cpu%d_dram_joules'%(i), 'cpu-energy-meter.out',  'cpu%d_dram_joules={pattern:F}'%(i)],
		])
	for args in COLUMNS:
		model.add_column(parsable_column(*args))
	traces = TableViewController(model=model, doc=doc)
	tab = Tabs(tabs=[
		Panel(child=traces.view, title='Traces'),
	])
	doc.add_root(tab)
	pass