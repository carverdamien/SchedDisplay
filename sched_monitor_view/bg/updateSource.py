from threading import Thread
import numpy as np
import Types

def plot(data, event, callback):
	args = (data, event, callback)
	return Thread(target=target, args=args)

def target(data, event_selected, callback):
	source_event_data = []
	for i in range(len(Types.EVENT)):
		x0 = np.array([])
		x1 = np.array([])
		y0 = np.array([])
		y1 = np.array([])
		if i in event_selected:
			for cpu in data:
				timestamp = np.array(data[cpu]['timestamp'])
				event = np.array(data[cpu]['event'])
				sel = event == i
				N = len(timestamp[sel])
				x0 = np.append(x0, timestamp[sel])
				x1 = np.append(x1, timestamp[sel])
				y0 = np.append(y0, float(cpu) * np.ones(N))
				y1 = np.append(y1, (float(cpu)+.25) * np.ones(N))
		source_event_data.append(dict(x0=x0, y0=y0, x1=x1, y1=y1))
	callback(source_event_data)
