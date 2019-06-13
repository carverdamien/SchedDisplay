from threading import Thread
import time, os

def feed(root, ext, callback):
	args = (root, ext, callback)
	return Thread(target=target, args=args)

def target(root, ext, callback):
	old = []
	while True:
		new = list(find_files(root,ext))
		if new != old:
			callback(new)
			old = new
		time.sleep(10)

def find_files(directory, ext):
	for root, dirs, files in os.walk(directory, topdown=False):
		for name in files:
			path = os.path.join(root, name)
			if ext == os.path.splitext(name)[1]:
				yield path
