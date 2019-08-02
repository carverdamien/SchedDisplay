from bokeh.models.widgets import PreText
import logging
from threading import Lock
from functools import partial
from tornado import gen
from smv.ViewController import ViewController

class ConsoleViewController(ViewController):
	def __init__(self, max_length=1024, doc=None):
		view = PreText()
		super(ConsoleViewController, self).__init__(view, doc)
		self.max_length = max_length
		self.buffer = []
		self.lock = Lock()

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
