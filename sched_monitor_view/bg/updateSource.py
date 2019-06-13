from threading import Thread
import numpy as np
import EventTypes

def plot(data, event, callback):
	args = (data, event, callback)
	return Thread(target=target, args=args)

def target(data, event, callback):
	source_event_data = [
		dict(x0=[0], y0=[0], x1=[1], y1=[1])
		for i in range(len(EventTypes.EVENT))
	]
	callback(source_event_data)
