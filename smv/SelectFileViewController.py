from smv.ViewController import ViewController
from bokeh.models.widgets import Select, Button, TextAreaInput
from bokeh.layouts import row, column
import os, io, stat, tarfile, json

def find_files(directory, ext):
	for root, dirs, files in os.walk(directory, topdown=False):
		for name in files:
			path = os.path.join(root, name)
			if ext == os.path.splitext(name)[1]:
				yield path

def preview_size(path):
	if path is None:
		return 'There is nothing to preview'
	else:
		return 'File {} is {} bytes'.format(path, os.stat(path)[stat.ST_SIZE])

def preview(path):
	if path is None:
		return 'There is nothing to preview'
	_, ext = os.path.splitext(path)
	if ext in ['.json']:
		with open(path, 'r') as f:
			return f.read()
	elif ext in ['.tar','.tgz']:
		msg = ['File {} is {} bytes and contains:'.format(path, os.stat(path)[stat.ST_SIZE])]
		with tarfile.open(path, 'r') as tar:
			for tarinfo in tar:
				extend = [tarinfo.name]
				_, ext = os.path.splitext(tarinfo.name)
				if tarinfo.isreg():
					if ext in ['.json']:
						with tar.extractfile(tarinfo.name) as f:
							extend.extend([str(json.load(f))])
					else:
						try:
							size = min(tarinfo.size, 2**20)
							with tar.extractfile(tarinfo.name) as f:
								extend.extend([f.read(size).decode()])
						except Exception as e:
							pass
				msg.extend(extend)
		return "\n".join(msg)
	else:
		return preview_size(path)

class SelectFileViewController(ViewController):
	"""docstring for SelectFileViewController"""
	def __init__(self, directory, ext, doc=None, log=None):
		options=sorted(list(find_files(directory,ext)))
		options0 = None
		if len(options) > 0:
			options0 = options[0]
		select = Select(
			title="Select File:",
			value=options0,
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
		preview_button = Button(
			label='Preview',
			align="end",
			button_type="success",
			width=100,
			width_policy="fixed",
			height=40,
			height_policy="fixed",
		)
		file_preview = TextAreaInput(
			value=preview_size(options0),
			sizing_mode='stretch_both',
			max_length=16*2**20,
			disabled=False,
		)
		view = column(
			row(select,
			    preview_button,
			    select_button,
			    sizing_mode = 'scale_width',
			),
			file_preview,
			sizing_mode='stretch_both',
		)
		super(SelectFileViewController, self).__init__(view, doc, log)
		self.select = select
		self.select.on_change('value', self.select_changed_valued)
		self.preview_button = preview_button
		self.preview_button.on_click(self.preview_button_on_click)
		self.select_button = select_button
		self.on_selected_callback = None
		self.select_button.on_click(self.select_on_click)
		self.file_preview = file_preview

	def select_changed_valued(self, attr, old, new):
		self.file_preview.value = preview_size(self.select.value)

	def preview_button_on_click(self, new):
		self.file_preview.value = preview(self.select.value)

	def on_selected(self, callback):
		self.on_selected_callback = callback

	def select_on_click(self):
		if self.on_selected_callback is None:
			return
		path = self.select.value
		self.on_selected_callback(path)
