from bokeh.models import Panel, Tabs
from smv.ConsoleViewController import ConsoleViewController, logFunctionCall
from smv.LoadFileViewController import LoadFileViewController
from smv.SelectFileViewController import SelectFileViewController
from smv.FigureViewController import FigureViewController
from smv.DataFrame import DataFrame
import json
import pandas as pd
import dask
from multiprocessing import cpu_count

def modify_doc(doc):
	nr_cpu = 160
	px_height = 4
	height = (nr_cpu+2)*px_height
	width = 1080 # May want to make width custumizable?
	state = {
		'nr_cpu' : nr_cpu,
		'px_height' : px_height,
		'height' : height,
		'width' : width,
		'y0_shift' : 0. / float(px_height),
		'y1_shift' : 2. / float(px_height),
	}
	console = ConsoleViewController(doc=doc)
	log = console.write
	@logFunctionCall(log)
	def lines_from_df(df):
		lines = pd.DataFrame({
			'x0':df['timestamp'],
			'x1':df['timestamp'],
			'y0':df['cpu']+state['y0_shift'],
			'y1':df['cpu']+state['y1_shift'],
			'category':df['event'],
		})
		lines['category'] = lines['category'].astype('category')
		lines = dask.dataframe.from_pandas(lines, npartitions=cpu_count())
		lines.persist() # Persist multiple Dask collections into memory
		return lines
	load_trace = SelectFileViewController('./examples/trace','.tar',doc=doc, log=log)
	load_plot = LoadFileViewController('./examples/plot','.json',doc=doc, log=log)
	figure = FigureViewController(doc=doc, log=log)
	tab = Tabs(tabs=[
		Panel(child=load_trace.view, title='Select TAR'),
		Panel(child=load_plot.view,  title='Select JSON'),
		Panel(child=figure.view,     title='Figure'),
		Panel(child=console.view,    title='Console'),
	])
	@logFunctionCall(log)
	def on_selected_trace(path):
		df = DataFrame(path)
		console.write('{} records in trace'.format(len(df)))
		state['df'] = df
		state['lines'] = lines_from_df(df)
	load_trace.on_selected(on_selected_trace)
	@logFunctionCall(log)
	def on_loaded_plot(io):
		plot = io.read()
		console.write('Plot:{}'.format(plot))
		try:
			plot = json.loads(plot)
		except Exception as e:
			console.write(e)
			return
		figure.plot(state['width'], state['height'], state['lines'])
	load_plot.on_loaded(on_loaded_plot)
	doc.add_root(tab)
	pass
