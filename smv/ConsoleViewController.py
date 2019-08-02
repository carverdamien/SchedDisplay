from bokeh.models.widgets import PreText
from functools import partial
from tornado import gen
import logging
from threading import Lock

class ConsoleViewController(object):
	def __init__(self, max_length=1024, doc=None):
		super(ConsoleViewController, self).__init__()
		self.max_length = max_length
		self.buffer = []
		self.lock = Lock()
		self.view = PreText()
		self.doc = doc

	def hide(self):
		if self.doc is not None:
			@gen.coroutine
			def coroutine():
				self.view.visible = False
			self.doc.add_next_tick_callback(partial(coroutine))

	def show(self):
		if self.doc is not None:
			@gen.coroutine
			def coroutine():
				self.view.visible = True
			self.doc.add_next_tick_callback(partial(coroutine))

	def write(self, *args):
		self.lock.acquire()
		msg = ''.join([str(a) for a in args])
		logging.info(msg)
		self.buffer.append(msg)
		while len(self.buffer) > self.max_length:
			self.buffer.pop(0)
		if self.doc is not None:
			@gen.coroutine
			def coroutine():
				self.view.text = '\n'.join(self.buffer)
			self.doc.add_next_tick_callback(partial(coroutine))
		self.lock.release()
