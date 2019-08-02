from smv.ViewController import ViewController
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.widgets import Select, Button
from bokeh.layouts import row
import os, io, base64
from threading import Thread

def find_files(directory, ext):
	for root, dirs, files in os.walk(directory, topdown=False):
		for name in files:
			path = os.path.join(root, name)
			if ext == os.path.splitext(name)[1]:
				yield path

# Special thanks to Kevin Anderson
CUSTOM_JS_CODE = """
function read_file(filename) {
    var reader = new FileReader();
    reader.onload = load_handler;
    reader.onerror = error_handler;
    // readAsDataURL represents the file's data as a base64 encoded string
    reader.readAsDataURL(filename);
}
function load_handler(event) {
    var b64string = event.target.result;
    file_source.data = {'file_contents' : [b64string], 'file_name':[input.files[0].name]};
    file_source.trigger("change");
}
function error_handler(evt) {
    if(evt.target.error.name == "NotReadableError") {
        alert("Can't read file!");
    }
}
var input = document.createElement('input');
input.setAttribute('type', 'file');
input.onchange = function(){
    if (window.FileReader) {
        read_file(input.files[0]);
    } else {
        alert('FileReader is not supported in this browser');
    }
}
input.click();
"""

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
		select_button = Button(
			label='Select',
			align="end",
			button_type="success",
			width=100,
			width_policy="fixed",
			height=40,
			height_policy="fixed",
		)
		upload_button = Button(
			label='Upload',
			align="end",
			button_type="success",
			width=100,
			width_policy="fixed",
			height=40,
			height_policy="fixed",
	    )
		view = row(select, select_button, upload_button, sizing_mode = 'scale_width',)
		super(LoadFileViewController, self).__init__(view, doc)
		self.select = select
		self.select_button = select_button
		self.upload_button = upload_button
		self.datasource = ColumnDataSource({'file_contents':[], 'file_name':[]})
		self.on_loaded_callback = None
		self.select_button.on_click(self.select_on_click)
		self.upload_button.callback = CustomJS(args=dict(file_source=self.datasource), code=CUSTOM_JS_CODE)
		self.datasource.on_change('data', self.file_callback)

	def on_loaded(self, callback):
		self.on_loaded_callback = callback

	def select_on_click(self):
		if self.on_loaded_callback is None:
			return
		path = self.select.value
		def target():
			with open(path,'r') as f:
				self.on_loaded_callback(f)
		Thread(target=target).start()

	def file_callback(self,attr,old,new):
		if self.on_loaded_callback is None:
			return
		filename = self.datasource.data['file_name'][0]
		raw_contents = self.datasource.data['file_contents'][0]
		# remove the prefix that JS adds
		prefix, b64_contents = raw_contents.split(",", 1)
		file_contents = base64.b64decode(b64_contents)
		file_io = io.BytesIO(file_contents)
		self.on_loaded_callback(file_io)