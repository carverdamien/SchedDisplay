import logging
from bokeh.server.server import Server
from tornado.web import RequestHandler
from smv.apps.test_ConsoleView import modify_doc as test_ConsoleView
from smv.apps.test_LoadFileView import modify_doc as test_LoadFileView
from smv.apps.test_FigureViewController import modify_doc as test_FigureViewController
from smv.apps.v0 import modify_doc as v0
from smv.apps.traces import modify_doc as traces
from smv.apps.frqdiff import modify_doc as frqdiff

class StaticHandler(RequestHandler):
    def initialize(self, path):
        self.path = path
    def get(self):
    	with open(self.path) as f:
    		self.write(f.read())

def main():
	FORMAT = '%(asctime)-15s %(message)s'
	logging.basicConfig(format=FORMAT, level=logging.DEBUG)
	server = Server(
	applications={
		'/test_ConsoleView'          : test_ConsoleView,
		'/test_LoadFileView'         : test_LoadFileView,
		'/test_FigureViewController' : test_FigureViewController,
		'/v0'                        : v0,
		'/traces'                    : traces,
		'/frqdiff'                   : frqdiff,
	},
	extra_patterns=[('/static/js/worker.js', StaticHandler, {"path":'./static/js/worker.js'})],
	)
	server.start()
	server.io_loop.start()
	pass
