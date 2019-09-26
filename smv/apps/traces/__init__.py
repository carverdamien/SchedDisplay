from smv.TableModel import TracesModel, Column, parsable_column, dependable_column, json_column
from smv.TableViewController import TableViewController
from smv.ScatterViewController import ScatterViewController
from bokeh.models import Panel, Tabs
import numpy as np
import itertools

def modify_doc(doc):
	model = TracesModel()
	# TODO: Make model's columns customizable by the user
	def fname(i):
		return i
	model.add_column(Column(dtype=str, function=fname))
	PERF = [
		[float, 'usr_bin_time',  'time.err', '{pattern:F}'],
		[float, 'sysbench_trps', 'run.out',  '{:s}transactions:{:s}{:d}{:s}({pattern:F} per sec.)'],
	]
	PACKAGE_ENERGY = [
		[float, 'cpu%d_package_joules'%(i), 'cpu-energy-meter.out',  'cpu%d_package_joules={pattern:F}'%(i)]
		for i in range(4)
	]
	DRAM_ENERGY    = [
		[float, 'cpu%d_dram_joules'%(i),    'cpu-energy-meter.out',  'cpu%d_dram_joules={pattern:F}'%(i)   ]
		for i in range(4)
	]
	COLUMNS = PERF + PACKAGE_ENERGY + DRAM_ENERGY
	for args in COLUMNS:
		model.add_column(parsable_column(*args))
	MAX_PHORONIX = 2
	PHORONIX_TEST = [
		[str, f'phoro_test{i}', 'phoronix.json', ['results',i,'test']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX_ARGS = [
		[str, f'phoro_args{i}', 'phoronix.json', ['results',i,'arguments']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX_UNITS = [
		[str, f'phoro_units{i}', 'phoronix.json', ['results',i,'units']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX_VALUE = [
		[float, f'phoro_value{i}', 'phoronix.json', ['results',i,'results','schedrecord','value']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX = [i for j in itertools.zip_longest(PHORONIX_TEST,PHORONIX_ARGS,PHORONIX_UNITS,PHORONIX_VALUE) for i in j]
	JSONS = PHORONIX
	for args in JSONS:
		model.add_column(json_column(*args))
	TOTAL_ENERGY = [
		[float, 'total_package_joules',lambda row: np.sum([row['cpu%d_package_joules'%(i)] for i in range(4)])],
		[float, 'total_dram_joules',   lambda row: np.sum([row['cpu%d_dram_joules'%(i)] for i in range(4)])],
		[float, 'total_joules',        lambda row: np.sum([row[c] for c in ['total_package_joules', 'total_dram_joules']])],
	]
	for args in TOTAL_ENERGY:
		model.add_dependable_column(dependable_column(*args))
	# end of model customization
	traces = TableViewController(model=model, doc=doc)
	scatter = ScatterViewController(model=model, doc=doc)
	tab = Tabs(tabs=[
		Panel(child=traces.view, title='Traces'),
		Panel(child=scatter.view, title='Scatter'),
	])
	doc.add_root(tab)
	pass