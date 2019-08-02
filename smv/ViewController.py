from functools import partial
from tornado import gen

class ViewController(object):
	"""docstring for ViewController"""
	def __init__(self, view, doc):
		super(ViewController, self).__init__()
		self.view = view
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
