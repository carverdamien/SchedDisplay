from bokeh.models import Panel, Tabs
from bokeh.models.widgets import DataTable
from smv.ConsoleViewController import ConsoleViewController, logFunctionCall
from smv.LoadFileViewController import LoadFileViewController
from smv.SelectFileViewController import SelectFileViewController
from smv.FigureViewController import FigureViewController
import smv.DataDict as DataDict
import smv.LinesFrame as LinesFrame
import json, os
import pandas as pd
# import dask
# from multiprocessing import cpu_count
from threading import Thread

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
	def LinesFrame_from_df(df, config):
		return LinesFrame.from_df(df, config, log)
	load_cache = SelectFileViewController('./examples/cache','.json',doc=doc, log=log)
	load_trace = SelectFileViewController('./examples/trace','.tar',doc=doc, log=log)
	load_config = LoadFileViewController('./examples/config','.json',doc=doc, log=log)
	figure = FigureViewController(get_image_ranges=get_image_ranges, doc=doc, log=log)
	# figure.table = DataTable(source=figure.source)
	tab = Tabs(tabs=[
		Panel(child=load_trace.view, title='Select TAR'),
		Panel(child=load_config.view,  title='Select JSON'),
		Panel(child=load_cache.view,  title='Cache'),
		Panel(child=figure.view,     title='Figure'),
		# Panel(child=figure.table,    title='Sample'),
		Panel(child=console.view,    title='Console'),
	])
	@logFunctionCall(log)
	def cache_put():
		try:
			key = hash(state['path'] + json.dumps({k:state[k] for k in state if k not in ['df','lines']}))
			log('Saving: {}'.format(key))
			if 'df' in state:
				state['df'].to_parquet('./examples/cache/{}.df.parquet'.format(key),compression='UNCOMPRESSED')
			state['lines'].to_parquet('./examples/cache/{}.lines.parquet'.format(key),compression='UNCOMPRESSED')
			# dask.dataframe.to_parquet(state['lines'], './examples/cache/{}.lines.parquet'.format(key))
			with open('./examples/cache/{}.json'.format(key),'w') as f:
				json.dump({k:state[k] for k in state if k not in ['df','lines']},f)
				log('Saved: {}'.format(key))
		except Exception as e:
			log(e)
	@logFunctionCall(log)
	def cache_get(path):
		try:
			lines_path = os.path.splitext(path)[0] + '.lines.parquet'
			with open(path) as f:
				state = json.load(f)
				state['lines'] = pd.read_parquet(lines_path)
				state['lines']['c'] = state['lines']['c'].astype(pd.CategoricalDtype(ordered=True))
				figure.plot(state['config'], state['width'], state['height'], state['lines'])
		except Exception as e:
			log(e)
	load_cache.on_selected(cache_get)
	@logFunctionCall(log)
	def on_selected_trace(path):
		df = pd.DataFrame(DataDict.from_tar(path))
		console.write('{} records in trace'.format(len(df)))
		state['df'] = df
		state['path'] = path
	load_trace.on_selected(on_selected_trace)
	@logFunctionCall(log)
	def on_loaded_config(io):
		config = io.read()
		console.write('config:{}'.format(config))
		try:
			state['config'] = json.loads(config)
			if 'df' not in state:
				on_selected_trace(state['path'])
			state['lines'] = LinesFrame_from_df(state['df'], state['config'])
			Thread(target=cache_put).start()
			del state['df'] # Save memory
			figure.plot(state['config'], state['width'], state['height'], state['lines'])
		except Exception as e:
			console.write(e)
	load_config.on_loaded(on_loaded_config)
	doc.add_root(tab)
	pass
