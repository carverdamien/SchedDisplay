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
console.log(file_source)
function read_file(filename) {
    var reader = new FileReader();
    reader.onload = load_handler;
    reader.onerror = error_handler;
    // readAsDataURL represents the file's data as a base64 encoded string
    reader.readAsDataURL(filename);
}
function load_handler(event) {
    var b64string = event.target.result;
    update_file_source(b64string);
}
function update_file_source(b64string) {
    var i=0;
    var block_size=1048576;
    while (i<b64string.length) {
    	block = b64string.substring(i,i+block_size)
    	remaining = b64string.length-(i+block_size)
		file_source.stream({'i':[i], 'block':[block],'remaining':[remaining]})
    	file_source.change.emit();
    	i+=block_size;
    }
    console.log('update_file_source done');
}
async function stream(i, block, remaining) {
	console.log('uploading block',i)
	file_source.stream({'i':[i], 'block':[block],'remaining':[remaining]})
    file_source.change.emit();
}
function error_handler(evt) {
    if(evt.target.error.name == "NotReadableError") {
        alert("Can't read file!");
    }
}
var input = document.createElement('input');
input.setAttribute('type', 'file');
input.onchange = function(){
	file_source.data = {'i':[], 'block':[],'remaining':[]}
    file_source.change.emit();
	if (window.Worker) {
		const myWorker = new Worker("/static/js/worker.js");
		var calls = 0;
		// myWorker.postMessage([file_source, input.files[0]])
		myWorker.postMessage(['NO_file_source', input.files[0]])
		myWorker.onmessage = function(e) {
			//update_file_source(e.data)
			//function f() { stream(e.data[0],e.data[1],e.data[2]); };setTimeout(f, 1000);
			stream(e.data[0],e.data[1],e.data[2]);
			calls += 1;
			if (calls==2) {
				alert('Big File detected: check your client console for progression. On chrome: Ctrl+Shift+J or Cmd+Option+J. On firefox Ctrl+Shift+K or Cmd+Opt+K')
			}
		}
	} else {
		alert("Your browser doesn't support web workers.");
		if (window.FileReader) {
        	read_file(input.files[0]);
    	} else {
       		alert('FileReader is not supported in this browser');
    	}	
	}
}
input.click();
"""

class LoadFileViewController(ViewController):
	"""docstring for LoadFileViewController"""
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
		super(LoadFileViewController, self).__init__(view, doc, log)
		self.select = select
		self.select_button = select_button
		self.upload_button = upload_button
		# self.datasource = ColumnDataSource({'file_contents':[], 'file_name':[]})
		# self.datasource = ColumnDataSource({'file_contents':[]})
		self.datasource = ColumnDataSource({'i':[], 'block':[],'remaining':[]})
		self.on_loaded_callback = None
		self.select_button.on_click(self.select_on_click)
		self.upload_button.callback = (CustomJS(args=dict(file_source=self.datasource), code=CUSTOM_JS_CODE))
		self.datasource.on_change('data', self.file_callback)

	def on_loaded(self, callback):
		self.on_loaded_callback = callback

	def select_on_click(self):
		if self.on_loaded_callback is None:
			return
		path = self.select.value
		def target():
			with open(path,'rb') as f:
				self.on_loaded_callback(f)
		Thread(target=target).start()

	def file_callback(self,attr,old,new):
		if self.on_loaded_callback is None:
			return
		if len(self.datasource.data['remaining']) == 0:
			return
		remaining = self.datasource.data['remaining'][-1]
		if remaining > 0:
			self.log('{} bytes remaining'.format(remaining))
			return
		raw_contents = ''.join(self.datasource.data['block'])
		# remove the prefix that JS adds
		prefix, b64_contents = raw_contents.split(",", 1)
		file_contents = base64.b64decode(b64_contents)
		file_io = io.BytesIO(file_contents)
		self.on_loaded_callback(file_io)
		# self.datasource.data = {'i':[], 'block':[],'remaining':[]}