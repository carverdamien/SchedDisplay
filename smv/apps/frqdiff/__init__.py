from smv.TableModel import TableModel, Column, parsable_column, ColumnNotFoundException, FLOAT, STRING
from smv.TableViewController import TableViewController
from smv.ScatterViewController import ScatterViewController
from bokeh.models import Panel, Tabs
import numpy as np
import itertools
import re, os, tarfile, json, traceback, parse

def json_column(dtype, name, i, basename, keys):
	def function(index, r):
		path = index[i]
		try:
			with tarfile.open(path, 'r:') as tar:
				for tarinfo in tar:
					if os.path.basename(tarinfo.name) != basename:
						continue
					with tar.extractfile(tarinfo.name) as f:
						value = json.load(f)
						for k in keys:
							value = value[k]
						return value
					break
		except Exception as e:
			# print(traceback.format_exc())
			pass
		raise ColumnNotFoundException()
	function.__name__ = name
	return Column(dtype=dtype, function=function)

def parsable_column(dtype, name, i, basename, pattern):
	def function(index, r):
		path = index[i]
		try:
			with tarfile.open(path, 'r:') as tar:
				for tarinfo in tar:
					if os.path.basename(tarinfo.name) != basename:
						continue
					with tar.extractfile(tarinfo.name) as f:
						re = parse.compile(pattern)
						for line in f.read().decode().split('\n'):
							r = re.parse(line)
							if r is not None:
								return r.named['pattern']
					break
		except Exception as e:
			print(traceback.format_exc())
			pass
		raise ColumnNotFoundException()
	function.__name__ = name
	return Column(dtype=dtype, function=function)
def modify_doc(doc):
	PATTERN = '.*BENCH=phoronix/POWER=.*/MONITORING=.*/PHORONIX=.*/.*/.*.tar'
	# PATTERN = '.*BENCH=phoronix/POWER=.*/MONITORING=.*/PHORONIX=redis/.*/.*.tar' # debug
	def find_files(directory, ext, regexp=".*"):
		regexp = re.compile(regexp)
		for root, dirs, files in os.walk(directory, topdown=False):
			for name in files:
				path = os.path.join(root, name)
				if ext == os.path.splitext(name)[1] and regexp.match(path):
					yield path
	def PHORONIXES(fname):
		return np.unique([re.search(f'(?<=PHORONIX=)[^/]+', f).group(0) for f in fname])
	def fcouple():
		_index_ = []
		fname = sorted(list(find_files('./examples/trace', '.tar', PATTERN)))
		kernel = "4.19.0-linux-4.19-ipanema-g2bd98bf652cb"
		for p in PHORONIXES(fname):
			powersave = re.compile(f'.*BENCH=phoronix/POWER=powersave-y/MONITORING=cpu-energy-meter/PHORONIX={p}/{kernel}/1.tar')
			performance = re.compile(f'.*BENCH=phoronix/POWER=performance-n/MONITORING=cpu-energy-meter/PHORONIX={p}/{kernel}/1.tar')
			fpowersave = None
			fperformance = None
			for f in fname:
				if fpowersave is None and powersave.match(f):
					fpowersave = f
				elif fperformance is None and performance.match(f):
					fperformance = f
				if fperformance is not None and fpowersave is not None:
					_index_.append((fpowersave, fperformance))
					break
		return _index_
	def get_tau(path):
		tau = []
		try:
			with tarfile.open(path, 'r:') as tar:
				for tarinfo in tar:
					if os.path.basename(tarinfo.name) != 'phoronix.json':
						continue
					with tar.extractfile(tarinfo.name) as f:
							value = json.load(f)
							for results in value['results']:
								tau.append((results['test'], results['arguments'], results['units']))
		except Exception as e:
			print(traceback.format_exc())
		return tau
	def index():
		_index_ = []
		for fpowersave, fperformance in fcouple():
			tau_powersave   = get_tau(fpowersave)
			tau_performance = get_tau(fperformance)
			for tau in tau_powersave:
				if tau in tau_performance:
					_index_.append((fpowersave, fperformance, *tau))
		print(_index_)
		return _index_
	model = TableModel(index=index)
	BASE = [
		[STRING, 'test', lambda index, row: index[2]],
		[STRING, 'arguments', lambda index, row: index[3]],
		[STRING, 'units', lambda index, row: index[4]],
	]
	for args in BASE:
		kwargs = {'dtype':args[0],'name':args[1],'function':args[2]}
		model.add_column(Column(**kwargs))
	WHAT = ['powersave', 'performance']
	USR_BIN_TIME = [
		[FLOAT, 'usr_bin_time_%s'%(WHAT[j]), j, 'time.err', '{pattern:F}']
		for j in range(2)
	]
	#PACKAGE_ENERGY = [
	#	[FLOAT, 'cpu%d_package_joules_%s'%(i,WHAT[j]), j, 'cpu-energy-meter.out',  'cpu%d_package_joules={pattern:F}'%(i)]
	#	for i in range(4)
	#	for j in range(2)
	#]
	#DRAM_ENERGY    = [
	#	[FLOAT, 'cpu%d_dram_joules_%s'%(i,WHAT[j]), j,    'cpu-energy-meter.out',  'cpu%d_dram_joules={pattern:F}'%(i)   ]
	#	for i in range(4)
	#	for j in range(2)
	#]
	# COLUMNS = USR_BIN_TIME # + PACKAGE_ENERGY + DRAM_ENERGY
	# for args in COLUMNS:
	# 	model.add_column(parsable_column(*args))
	#	pass
	#TOTAL_ENERGY = [
	#	[FLOAT, 'total_package_joules_powersave',lambda inedx, row: np.sum([row['cpu%d_package_joules_powersave'%(i)] for i in range(4)])],
	#	[FLOAT, 'total_package_joules_performance',lambda inedx, row: np.sum([row['cpu%d_package_joules_performance'%(i)] for i in range(4)])],
	#	[FLOAT, 'total_dram_joules_powersave',lambda inedx, row: np.sum([row['cpu%d_dram_joules_powersave'%(i)] for i in range(4)])],
	#	[FLOAT, 'total_dram_joules_performance',lambda inedx, row: np.sum([row['cpu%d_dram_joules_performance'%(i)] for i in range(4)])],
	#	[FLOAT, 'total_joules_powersave',        lambda inedx, row: np.sum([row[c] for c in ['total_package_joules_powersave', 'total_dram_joules_powersave']])],
	#	[FLOAT, 'total_joules_performance',        lambda inedx, row: np.sum([row[c] for c in ['total_package_joules_performance', 'total_dram_joules_performance']])]
	#]
	#TOTAL_ENERGY = []
	#for args in TOTAL_ENERGY:
	#	kwargs = {'dtype':args[0],'name':args[1],'function':args[2]}
	#	model.add_column(Column(**kwargs))
	def phoronix(i):
		def function(index, row):
			fpowersave, fperformance, test, arguments, units = index
			if i == 0:
				path = fpowersave
			else:
				path = fperformance
			with tarfile.open(path, 'r:') as tar:
				for tarinfo in tar:
					if os.path.basename(tarinfo.name) != 'phoronix.json':
						continue
					with tar.extractfile(tarinfo.name) as f:
							value = json.load(f)
							for results in value['results']:
								if results['test'] == test and results['arguments'] == arguments and results['units'] == units:
									return results['results']['schedrecord']['value']
			raise ColumnNotFoundException()
		return function
	PHORONIX_VALUE = [
		[FLOAT, 'perf_value_powersave', phoronix(0)],
		[FLOAT, 'perf_value_performance', phoronix(1)],
	]
	for args in PHORONIX_VALUE:
		kwargs = {'dtype':args[0],'name':args[1],'function':args[2]}
		model.add_column(Column(**kwargs))
		pass
	DIFF = [
		[FLOAT, 'diff_ratio', lambda index, row: (row['perf_value_powersave'] - row['perf_value_performance'])/row['perf_value_powersave']]
	]
	for args in DIFF:
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
