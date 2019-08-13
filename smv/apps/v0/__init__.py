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
	console = ConsoleViewController(doc=doc)
	log = console.write
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
	def get_image_ranges(FVC):
		xmin = FVC.fig.x_range.start
		xmax = FVC.fig.x_range.end
		# ymin = FVC.fig.y_range.start
		# ymax = FVC.fig.y_range.end
		ymin = -1
		ymax = nr_cpu+1
		if FVC.fig.y_range.end > ymax:
			FVC.fig.y_range.end = ymax
		if FVC.fig.y_range.start < ymin:
			FVC.fig.y_range.start = ymin
		w = FVC.fig.plot_width
		h = FVC.fig.plot_height
		return {
			'xmin':xmin,
			'xmax':xmax,
			'ymin':FVC.fig.y_range.start,
			'ymax':FVC.fig.y_range.end,
			'w':w,
			'h':h,
		}
	@logFunctionCall(log)
	def lines_from_df(df):
		df['timestamp'] = df['timestamp']-min(df['timestamp'])
		lines = pd.DataFrame({
			'x0':df['timestamp'],
			'x1':df['timestamp'],
			'y0':df['cpu']+state['y0_shift'],
			'y1':df['cpu']+state['y1_shift'],
			'c':df['event'],
		})
		lines['c'] = lines['c'].astype('category')
		lines = dask.dataframe.from_pandas(lines, npartitions=cpu_count())
		lines.persist() # Persist multiple Dask collections into memory
		return lines
	load_trace = SelectFileViewController('./examples/trace','.tar',doc=doc, log=log)
	load_plot = LoadFileViewController('./examples/plot','.json',doc=doc, log=log)
	figure = FigureViewController(get_image_ranges=get_image_ranges, doc=doc, log=log)
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
