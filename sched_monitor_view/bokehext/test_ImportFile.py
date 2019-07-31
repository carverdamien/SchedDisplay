from bokeh.layouts import row
from bokeh.io import curdoc
from ImportFile import ImportFile

importfile = ImportFile(label="Upload", button_type="success")
curdoc().add_root(row(importfile.button))
