from bokeh.server.server import Server
from smv.apps.app0 import modify_doc as app0
from smv.apps.app1 import modify_doc as app1

def main():
	server = Server({
		'/app0' : app0,
		'/app1' : app1,
	})
	server.start()
	server.io_loop.start()
	pass
