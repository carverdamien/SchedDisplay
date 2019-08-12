from smv.ViewController import ViewController
from bokeh.models.widgets import Select, Button
from bokeh.layouts import row
import os, io

def find_files(directory, ext):
	for root, dirs, files in os.walk(directory, topdown=False):
		for name in files:
			path = os.path.join(root, name)
			if ext == os.path.splitext(name)[1]:
				yield path

class SelectFileViewController(ViewController):
	"""docstring for SelectFileViewController"""
	def __init__(self, directory, ext, doc=None, log=None):
		options=sorted(list(find_files(directory,ext)))
		select = Select(
			title="Select File:",
			value=options[0],
			options=options,
			height=40,
			height_policy="fixed",
		)
		select_button = Button(
			label='Select',
			align="end",
			button_type="success",
			width=100,
			width_policy="fixed",
			height=40,
			height_policy="fixed",
		)
		view = row(select, select_button, sizing_mode = 'scale_width',)
		super(SelectFileViewController, self).__init__(view, doc, log)
		self.select = select
		self.select_button = select_button
		self.on_selected_callback = None
		self.select_button.on_click(self.select_on_click)

	def on_selected(self, callback):
		self.on_selected_callback = callback

	def select_on_click(self):
		if self.on_selected_callback is None:
			return
		path = self.select.value
		self.on_selected_callback(path)
