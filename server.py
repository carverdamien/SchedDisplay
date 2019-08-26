#!/usr/bin/env python3
from bokeh.server.server import Server
from sched_monitor_view.main import modify_doc
import logging

server = Server(
	{'/sched_monitor_view': modify_doc},
#    io_loop=loop,        # Tornado IOLoop
#    **server_kwargs      # port, num_procs, etc.
)
# start timers and services and immediately return
server.start()

if __name__ == '__main__':
	FORMAT = '%(asctime)-15s %(message)s'
	logging.basicConfig(format=FORMAT, level=logging.DEBUG)
	logging.info('Opening Bokeh application on http://localhost:5006/')
	# server.io_loop.add_callback(server.show, "/")
	server.io_loop.start()
