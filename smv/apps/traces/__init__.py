from smv.TableModel import TableModel, Column, parsable_column, json_column, FLOAT, STRING
from smv.TableViewController import TableViewController
from smv.ScatterViewController import ScatterViewController
from bokeh.models import Panel, Tabs
import numpy as np
import itertools

def modify_doc(doc):
	def find_files(directory, ext, regexp=".*"):
		import re, os
		regexp = re.compile(regexp)
		for root, dirs, files in os.walk(directory, topdown=False):
			for name in files:
				path = os.path.join(root, name)
				if ext == os.path.splitext(name)[1] and regexp.match(path):
					yield path
	def index():
		return sorted(list(find_files('./examples/trace', '.tar', '.*phoronix.*')))
	model = TableModel(index=index)
	BASE = [
		[STRING, 'fname', lambda index, row: index]
	]
	for args in BASE:
		kwargs = {'dtype':args[0],'name':args[1],'function':args[2]}
		model.add_column(Column(**kwargs))
	PERF = [
		[FLOAT, 'usr_bin_time',  'time.err', '{pattern:F}'],
		[FLOAT, 'sysbench_trps', 'run.out',  '{:s}transactions:{:s}{:d}{:s}({pattern:F} per sec.)'],
	]
	PACKAGE_ENERGY = [
		[FLOAT, 'cpu%d_package_joules'%(i), 'cpu-energy-meter.out',  'cpu%d_package_joules={pattern:F}'%(i)]
		for i in range(4)
	]
	DRAM_ENERGY    = [
		[FLOAT, 'cpu%d_dram_joules'%(i),    'cpu-energy-meter.out',  'cpu%d_dram_joules={pattern:F}'%(i)   ]
		for i in range(4)
	]
	COLUMNS = PERF + PACKAGE_ENERGY + DRAM_ENERGY
	for args in COLUMNS:
		model.add_column(parsable_column(*args))
		pass
	MAX_PHORONIX = 2
	PHORONIX_TEST = [
		[STRING, f'phoro_test{i}', 'phoronix.json', ['results',i,'test']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX_ARGS = [
		[STRING, f'phoro_args{i}', 'phoronix.json', ['results',i,'arguments']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX_UNITS = [
		[STRING, f'phoro_units{i}', 'phoronix.json', ['results',i,'units']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX_VALUE = [
		[FLOAT, f'phoro_value{i}', 'phoronix.json', ['results',i,'results','schedrecord','value']]
		for i in range(MAX_PHORONIX)
	]
	PHORONIX = [i for j in itertools.zip_longest(PHORONIX_TEST,PHORONIX_ARGS,PHORONIX_UNITS,PHORONIX_VALUE) for i in j]
	JSONS = PHORONIX
	for args in JSONS:
		model.add_column(json_column(*args))
		pass
	TOTAL_ENERGY = [
		[FLOAT, 'total_package_joules',lambda inedx, row: np.sum([row['cpu%d_package_joules'%(i)] for i in range(4)])],
		[FLOAT, 'total_dram_joules',   lambda inedx, row: np.sum([row['cpu%d_dram_joules'%(i)] for i in range(4)])],
		[FLOAT, 'total_joules',        lambda inedx, row: np.sum([row[c] for c in ['total_package_joules', 'total_dram_joules']])],
	]
	for args in TOTAL_ENERGY:
		kwargs = {'dtype':args[0],'name':args[1],'function':args[2]}
		model.add_column(Column(**kwargs))
		pass
	# end of model customization
	traces = TableViewController(model=model, doc=doc)
	scatter = ScatterViewController(model=model, doc=doc)
	tab = Tabs(tabs=[
		Panel(child=traces.view, title='Traces'),
		Panel(child=scatter.view, title='Scatter'),
	])
	doc.add_root(tab)
	pass