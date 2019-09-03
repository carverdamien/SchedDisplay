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
from tornado import gen
from functools import partial
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
	def customize_ranges(ranges):
		ranges['ymax'] = min(ranges['ymax'], nr_cpu+1)
		ranges['ymin'] = max(ranges['ymin'], -1)
		return ranges
	@logFunctionCall(log)
	def LinesFrame_from_df(df, line_config):
		return LinesFrame.from_df(df, line_config, log)
	load_cache = SelectFileViewController('./examples/cache','.json',doc=doc, log=log)
	load_trace = SelectFileViewController('./examples/trace','.tar',doc=doc, log=log)
	load_line_config = LoadFileViewController('./examples/line','.json',doc=doc, log=log)
	figure = FigureViewController(customize_ranges=customize_ranges, doc=doc, log=log)
	# figure.table = DataTable(source=figure.source)
	tab = Tabs(tabs=[
		Panel(child=load_trace.view, title='Select TAR'),
		Panel(child=load_line_config.view,  title='Select JSON'),
		Panel(child=load_cache.view,  title='Cache'),
		Panel(child=figure.view,     title='Figure'),
		# Panel(child=figure.table,    title='Sample'),
		Panel(child=console.view,    title='Console'),
	])
	@logFunctionCall(log)
	def cache_put():
		fname = "cache_put"
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
			del state['df'] # Save memory
		except Exception as e:
			log('Exception({}) in {}: {}'.format(type(e), fname, e))
	@logFunctionCall(log)
	def cache_get(path):
		fname = "cache_get"
		try:
			lines_path = os.path.splitext(path)[0] + '.lines.parquet'
			with open(path) as f:
				state = json.load(f)
				state['lines'] = pd.read_parquet(lines_path)
				state['lines']['c'] = state['lines']['c'].astype(pd.CategoricalDtype(ordered=True))
				figure.plot(state['line_config'], state['width'], state['height'], state['lines'])
		except Exception as e:
			log('Exception({}) in {}: {}'.format(type(e), fname, e))
	load_cache.on_selected(cache_get)
	@logFunctionCall(log)
	def on_selected_trace(path):
		state['path'] = path
	load_trace.on_selected(on_selected_trace)
	@logFunctionCall(log)
	def on_loaded_line_config(io):
		fname = "on_loaded_line_config"
		line_config = io.read()
		log('line_config:{}'.format(line_config))
		try:
			state['line_config'] = json.loads(line_config)
			if 'df' not in state:
				df = pd.DataFrame(DataDict.from_tar(state['path'], state['line_config']['input']))
				log('{} records in trace'.format(len(df)))
				state['df'] = df
			state['lines'] = LinesFrame_from_df(state['df'], state['line_config'])
			# FIXME: Quick And Dirty set fig.title
			@gen.coroutine
			def coroutine():
				figure.fig.title.text = state['path']
			doc.add_next_tick_callback(partial(coroutine))
			figure.plot(state['line_config'], state['width'], state['height'], state['lines'])
			Thread(target=cache_put).start()
		except Exception as e:
			log('Exception({}) in {}: {}'.format(type(e), fname, e))
	load_line_config.on_loaded(on_loaded_line_config)
	doc.add_root(tab)
	pass
