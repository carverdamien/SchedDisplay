from smv.TableModel import TableModel, Column, parsable_column, json_column, FLOAT, STRING
from smv.TableViewController import TableViewController
from smv.ScatterViewController import ScatterViewController
from bokeh.models import Panel, Tabs
import numpy as np
import itertools
import re, os

def modify_doc(doc):
	PATTERN = '.*BENCH=phoronix/POWER=.*/MONITORING=.*/PHORONIX=.*/.*/.*.tar'
	PATTERN = '.*BENCH=phoronix/POWER=.*/MONITORING=.*/PHORONIX=redis/.*/.*.tar' # debug
	def find_files(directory, ext, regexp=".*"):
		regexp = re.compile(regexp)
		for root, dirs, files in os.walk(directory, topdown=False):
			for name in files:
				path = os.path.join(root, name)
				if ext == os.path.splitext(name)[1] and regexp.match(path):
					yield path
	def PHORONIXES(fname):
		return np.unique([re.search(f'(?<=PHORONIX=)[^/]+', f).group(0) for f in fname])
	def index():
		_index_ = []
		fname = sorted(list(find_files('./examples/trace', '.tar', PATTERN)))
		kernel = "4.19.0-linux-4.19-ipanema-g2bd98bf652cb"
		for p in PHORONIXES(fname):
			powersave = re.compile(f'.*BENCH=phoronix/POWER=powersave-y/MONITORING=cpu-energy-meter/PHORONIX={p}/{kernel}/1.tar')
			performance = re.compile(f'.*BENCH=phoronix/POWER=performance-n/MONITORING=cpu-energy-meter/PHORONIX={p}/{kernel}/1.tar')
			fpowersave = None
			fperformance = None
			for f in fname:
				print(f)
				if fpowersave is None and powersave.match(f):
					fpowersave = f
				elif fperformance is None and performance.match(f):
					fperformance = f
				if fperformance is not None and fpowersave is not None:
					_index_.append((fpowersave, fperformance))
					break
		return _index_
	model = TableModel(index=index)
	BASE = [
		[STRING, '_index_', lambda index, row: str(index)]
	]
	for args in BASE:
		kwargs = {'dtype':args[0],'name':args[1],'function':args[2]}
		model.add_column(Column(**kwargs))
	# end of model customization
	traces = TableViewController(model=model, doc=doc)
	scatter = ScatterViewController(model=model, doc=doc)
	tab = Tabs(tabs=[
		Panel(child=traces.view, title='Traces'),
		Panel(child=scatter.view, title='Scatter'),
	])
	doc.add_root(tab)
	pass
