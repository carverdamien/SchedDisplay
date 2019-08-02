import logging
from bokeh.server.server import Server
from smv.apps.test_ConsoleView import modify_doc as test_ConsoleView
from smv.apps.test_TabView import modify_doc as test_TabView

def main():
	FORMAT = '%(asctime)-15s %(message)s'
	logging.basicConfig(format=FORMAT, level=logging.DEBUG)
	server = Server({
		'/test_ConsoleView' : test_ConsoleView,
		'/test_TabView' : test_TabView,
	})
	server.start()
	server.io_loop.start()
	pass
