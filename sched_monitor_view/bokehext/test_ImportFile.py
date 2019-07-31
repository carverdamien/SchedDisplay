from bokeh.layouts import row
from bokeh.io import curdoc
from ImportFile import ImportFile

importfile = ImportFile()
curdoc().add_root(row(importfile.button))
