from functools import partial
from tornado import gen
import logging, time

def logginglog(*args):
	msg = ''.join([str(a) for a in args])
	logging.info(msg)

class ViewController(object):
	"""docstring for ViewController"""
	def __init__(self, view, doc=None, log=None, **kwargs):
		super(ViewController, self).__init__()
		self.view = view
		self.doc = doc
		if log is None:
			log = logginglog
		self.log = log

	def logFunctionCall(func):
		def f(self, *args, **kwargs):
			fname = func.__name__
			self.log('{} starts'.format(fname))
			starts = time.time()
			r = func(self, *args,**kwargs)
			ends = time.time()
			self.log('{} ends in {}s'.format(fname, ends-starts))
			return r
		return f

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
