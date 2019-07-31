from bokeh.layouts import row
from bokeh.io import curdoc
from UploadFile import UploadFile

uploadfile = UploadFile(label="Upload", button_type="success")
curdoc().add_root(row(uploadfile.button))
