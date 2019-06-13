from threading import Thread
import time, os

def feed(root, ext, callback):
	args = (root, ext, callback)
	return Thread(target=target, args=args)

def target(root, ext, callback):
	while True:
		callback(list(find_files(root,ext)))
		time.sleep(10)

def find_files(directory, ext):
	for root, dirs, files in os.walk(directory, topdown=False):
		for name in files:
			path = os.path.join(root, name)
			if ext == os.path.splitext(name)[1]:
				yield path
