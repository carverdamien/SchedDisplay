from bokeh.models.widgets import TextAreaInput
import logging, datetime
from threading import Lock
from functools import partial
from tornado import gen
from smv.ViewController import ViewController
import time

def logFunctionCall(log):
	def wrap(func):
		def f(*args, **kwargs):
			fname = func.__name__
			log('{} starts'.format(fname))
			starts = time.time()
			r = func(*args,**kwargs)
			ends = time.time()
			log('{} ends in {}s'.format(fname, ends-starts))
			return r
		return f
	return wrap

class ConsoleViewController(ViewController):
	def __init__(self, max_length=1024, doc=None, log=None):
		view = TextAreaInput(
			value='',
			sizing_mode='stretch_both',
			max_length=2**20,
		)
		super(ConsoleViewController, self).__init__(view, doc, log)
		self.max_length = max_length
		self.buffer = []
		self.lock = Lock()

	def write(self, *args):
		self.lock.acquire()
		header = datetime.datetime.now().isoformat() + ' '
		msg = ''.join([str(a) for a in args])
		logging.info(msg)
		self.buffer.append(header+msg)
		while len(self.buffer) > self.max_length:
			self.buffer.pop(0)
		if self.doc is not None:
			@gen.coroutine
			def coroutine():
				self.view.value = '\n'.join(reversed(self.buffer))
			self.doc.add_next_tick_callback(partial(coroutine))
		self.lock.release()
