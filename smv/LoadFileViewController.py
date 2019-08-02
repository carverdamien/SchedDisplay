from smv.ViewController import ViewController
from bokeh.models.widgets import Select, Button
from bokeh.layouts import row
import os
from threading import Thread

def find_files(directory, ext):
	for root, dirs, files in os.walk(directory, topdown=False):
		for name in files:
			path = os.path.join(root, name)
			if ext == os.path.splitext(name)[1]:
				yield path

class LoadFileViewController(ViewController):
	"""docstring for LoadFileViewController"""
	def __init__(self, directory, ext, doc=None):
		options=sorted(list(find_files(directory,ext)))
		select = Select(
			title="Select File:",
			value=options[0],
			options=options,
			height=40,
			height_policy="fixed",
		)
		button = Button(
			label='Select',
			align="end",
			button_type="success",
			width_policy="min",
			height=40,
			height_policy="fixed",
	    )
		view = row(select, button, sizing_mode = 'scale_width',)
		super(LoadFileViewController, self).__init__(view, doc)
		self.select = select
		self.button = button
		self.callback = None
		self.button.on_click(self.select_on_click)

	def on_loaded(self, callback):
		self.callback = callback

	def select_on_click(self):
		if self.callback is None:
			return
		path = self.select.value
		def target():
			with open(path,'r') as f:
				self.callback(f.read())
		Thread(target=target).start()
