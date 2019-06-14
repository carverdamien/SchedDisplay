from threading import Thread
import operator
import numpy as np
import Types

MAX_ITEM_PER_CORE=1000

def plot(data, event_selected, interval_selected, tlim, callback):
	args = (data, event_selected, interval_selected, tlim, callback)
	return Thread(target=target, args=args)

def target(data, event_selected, interval_selected, tlim, callback):
	source_event_data = []
	source_interval_data = []
	for event_id in range(len(Types.EVENT)):
		if event_id not in event_selected:
			source_event_data.append(dict(x0=[], y0=[], x1=[], y1=[]))
			continue
		x0 = np.array([])
		x1 = np.array([])
		y0 = np.array([])
		y1 = np.array([])
		y_offset = 0
		for path in data:
			for cpu in data[path]:
				timestamp = data[path][cpu]['timestamp']
				event = data[path][cpu]['event']
				# todo: searchsorted
				sel = (event == event_id) & (timestamp >= tlim[0]) & (timestamp <= tlim[1])
				if len(timestamp[sel]) <= MAX_ITEM_PER_CORE:
					continue
				timestamp = timestamp[sel][:MAX_ITEM_PER_CORE]
				tlim = (tlim[0], min(max(timestamp), tlim[1]))
		for path in data:
			for cpu in data[path]:
				timestamp = data[path][cpu]['timestamp']
				event = data[path][cpu]['event']
				# todo: searchsorted
				sel = (event == event_id) & (timestamp >= tlim[0]) & (timestamp <= tlim[1])
				timestamp = timestamp[sel]
				N = len(timestamp)
				x0 = np.append(x0, timestamp)
				y0 = np.append(y0, (float(cpu)+y_offset) * np.ones(N))
				y1 = np.append(y1, (float(cpu)+.75+y_offset) * np.ones(N))
			y_offset += len(data[path])
		source_event_data.append(dict(x0=x0, y0=y0, x1=x0, y1=y1))
	for i in range(len(Types.INTERVAL)):
		source_interval_data.append(dict(x0=[], y0=[], x1=[], y1=[]))
		# TODO
		# if i not in interval_selected or i not in HANDLER:
		# 	source_interval_data.append(dict(x0=[], y0=[], x1=[], y1=[]))
		# 	continue
		# source_interval_data.append(HANDLER[i](data, tlim))
	callback(source_event_data, source_interval_data, tlim)

def RQ_SIZE_eq_0(data, tlim):
	return interval(data, tlim, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.eq, 0)

def RQ_SIZE_gt_0(data, tlim):
	return interval(data, tlim, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.gt, 0)

def RQ_SIZE_eq_1(data, tlim):
	return interval(data, tlim, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.eq, 1)

def RQ_SIZE_gt_1(data, tlim):
	return interval(data, tlim, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.gt, 1)

def interval(data, tlim, event_id, measurement, op, value):
	r = {
		k : np.array([])
		for k in ['x0','x1','y0','y1']
	}
	# TODO
	tmax = max([
		data[path][cpu]['timestamp'][-1]
		for path in data
		for cpu in data[path]
	])
	y_offset = 0
	for path in data:
		for cpu in data[path]:
			timestamp = data[path][cpu]['timestamp']
			event = data[path][cpu]['event']
			# todo: searchsorted
			sel = (event == event_id) & (timestamp >= tlim[0]) & (timestamp <= tlim[1])
			timestamp = timestamp[sel]
			m = data[path][cpu][measurement][sel]
			_r = interval_per_cpu(float(cpu)+y_offset, timestamp, tmax, m, op, value)
			for k in r:
				r[k] = np.append(r[k], _r[k])
		y_offset+=len(data[path])
	return r

def interval_per_cpu(y_offset, timestamp, tmax, measurement, op, value):
	sel = op(measurement, value)
	if np.sum(sel) == 0:
		return dict(x0=[], y0=[], x1=[], y1=[])
	x0 = timestamp[sel]
	x1 = np.append(timestamp[1:],[tmax])[sel]
	N = len(x0)
	y0 = y_offset * np.ones(N)
	y1 = y_offset * np.ones(N)
	return dict(x0=x0, y0=y0, x1=x1, y1=y1)

HANDLER = {
	Types.ID_INTERVAL['RQ_SIZE=0'] : RQ_SIZE_eq_0,
	Types.ID_INTERVAL['RQ_SIZE>0'] : RQ_SIZE_gt_0,
	Types.ID_INTERVAL['RQ_SIZE=1'] : RQ_SIZE_eq_1,
	Types.ID_INTERVAL['RQ_SIZE>1'] : RQ_SIZE_gt_1,
}
