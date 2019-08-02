import logging
from bokeh.server.server import Server
from smv.apps.test_ConsoleView import modify_doc as test_ConsoleView
from smv.apps.test_TabView import modify_doc as test_TabView
from smv.apps.test_SeqView import modify_doc as test_SeqView
from smv.apps.test_SelectFileView import modify_doc as test_SelectFileView
from smv.apps.v0 import modify_doc as v0

def main():
	FORMAT = '%(asctime)-15s %(message)s'
	logging.basicConfig(format=FORMAT, level=logging.DEBUG)
	server = Server({
		'/test_ConsoleView'    : test_ConsoleView,
		'/test_TabView'        : test_TabView,
		'/test_SeqView'        : test_SeqView,
		'/test_SelectFileView' : test_SelectFileView,
		'/v0'                  : v0,
	})
	server.start()
	server.io_loop.start()
	pass
