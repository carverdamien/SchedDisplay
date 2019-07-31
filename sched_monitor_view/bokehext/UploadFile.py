from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.widgets import Button
import io
import base64

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

class UploadFile(object):
	"""docstring for UploadFile"""
	def __init__(self, *args, **kwargs):
		super(UploadFile, self).__init__()
		self.callback = lambda x,y:print(x, y.read())
		self.datasource = ColumnDataSource({'file_contents':[], 'file_name':[]})
		self.button = Button(*args, **kwargs)
		self.button.callback = CustomJS(args=dict(file_source=self.datasource), code=CUSTOM_JS_CODE)
		def file_callback(attr,old,new):
			filename = self.datasource.data['file_name'][0]
			raw_contents = self.datasource.data['file_contents'][0]
			# remove the prefix that JS adds  
			prefix, b64_contents = raw_contents.split(",", 1)
			file_contents = base64.b64decode(b64_contents)
			file_io = io.BytesIO(file_contents)
			self.callback(filename, file_io)
		self.datasource.on_change('data', file_callback)
