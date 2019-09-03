from smv.ConsoleViewController import ConsoleViewController, logFunctionCall
from smv.LoadFileViewController import LoadFileViewController
from smv.SelectFileViewController import SelectFileViewController
from bokeh.models import Panel, Tabs
import smv.DataDict as DataDict
import smv.LinesFrame as LinesFrame
import json, os
import pandas as pd

def modify_doc(doc):
	state = {
		'height' : 800,
		'width' : 600,
	}
	console = ConsoleViewController(doc=doc)
	log = console.write
	load_trace = SelectFileViewController('./examples/trace','.tar',doc=doc, log=log)
	load_point_config = LoadFileViewController('./examples/point','.json',doc=doc, log=log)
	tab = Tabs(tabs=[
		Panel(child=load_trace.view, title='Select TAR'),
		Panel(child=load_point_config.view,  title='Select JSON'),
		Panel(child=console.view,    title='Console'),
	])
	@logFunctionCall(log)
	def LinesFrame_from_df(df, point_config):
		return LinesFrame.from_df(df, point_config, log)
	@logFunctionCall(log)
	def on_selected_trace(path):
		state['path'] = path
	load_trace.on_selected(on_selected_trace)
	@logFunctionCall(log)
	def on_loaded_point_config(io):
		fname = "on_loaded_point_config"
		point_config = io.read()
		log('point_config:{}'.format(point_config))
		try:
			state['point_config'] = json.loads(point_config)
			if 'df' not in state:
				df = pd.DataFrame(DataDict.from_tar(state['path'], state['point_config']['input']))
				log('{} records in trace'.format(len(df)))
				state['df'] = df
			state['points'] = LinesFrame_from_df(state['df'], state['point_config'])
			log(state['points'])
		except Exception as e:
			log('Exception({}) in {}: {}'.format(type(e), fname, e))
	load_point_config.on_loaded(on_loaded_point_config)
	doc.add_root(tab)
	pass
