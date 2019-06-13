from threading import Thread
import operator
import numpy as np
import Types

def plot(data, event_selected, interval_selected, callback):
	args = (data, event_selected, interval_selected, callback)
	return Thread(target=target, args=args)

def target(data, event_selected, interval_selected, callback):
	source_event_data = []
	source_interval_data = []
	for i in range(len(Types.EVENT)):
		if i not in event_selected:
			source_event_data.append(dict(x0=[], y0=[], x1=[], y1=[]))
			continue
		x0 = np.array([])
		x1 = np.array([])
		y0 = np.array([])
		y1 = np.array([])
		for cpu in data:
			timestamp = np.array(data[cpu]['timestamp'])
			event = np.array(data[cpu]['event'])
			sel = event == i
			N = len(timestamp[sel])
			x0 = np.append(x0, timestamp[sel])
			x1 = np.append(x1, timestamp[sel])
			y0 = np.append(y0, float(cpu) * np.ones(N))
			y1 = np.append(y1, (float(cpu)+.75) * np.ones(N))
		source_event_data.append(dict(x0=x0, y0=y0, x1=x1, y1=y1))
	for i in range(len(Types.INTERVAL)):
		if i not in interval_selected or i not in HANDLER:
			source_interval_data.append(dict(x0=[], y0=[], x1=[], y1=[]))
			continue
		source_interval_data.append(HANDLER[i](data))
	callback(source_event_data, source_interval_data)

def RQ_SIZE_eq_0(data):
	return interval(data, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.eq, 0)

def RQ_SIZE_gt_0(data):
	return interval(data, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.gt, 0)

def RQ_SIZE_eq_1(data):
	return interval(data, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.eq, 1)

def RQ_SIZE_gt_1(data):
	return interval(data, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.gt, 1)

def interval(data, event_id, measurement, op, value):
	r = {
		k : np.array([])
		for k in ['x0','x1','y0','y1']
	}
	tmax = max([
		data[cpu]['timestamp'][-1]
		for cpu in data
	])
	for cpu in data:
		event = np.array(data[cpu]['event'])
		sel = event == event_id
		timestamp = np.array(data[cpu]['timestamp'])[sel]
		m = np.array(data[cpu][measurement])[sel]
		_r = interval_per_cpu(cpu, timestamp, tmax, m, op, value)
		for k in r:
			r[k] = np.append(r[k], _r[k])
	return r

def interval_per_cpu(cpu, timestamp, tmax, measurement, op, value):
	sel = op(measurement, value)
	if np.sum(sel) == 0:
		return dict(x0=[], y0=[], x1=[], y1=[])
	x0 = timestamp[sel]
	x1 = np.append(timestamp[1:],[tmax])[sel]
	N = len(x0)
	y0 = float(cpu) * np.ones(N)
	y1 = float(cpu) * np.ones(N)
	return dict(x0=x0, y0=y0, x1=x1, y1=y1)

HANDLER = {
	Types.ID_INTERVAL['RQ_SIZE=0'] : RQ_SIZE_eq_0,
	Types.ID_INTERVAL['RQ_SIZE>0'] : RQ_SIZE_gt_0,
	Types.ID_INTERVAL['RQ_SIZE=1'] : RQ_SIZE_eq_1,
	Types.ID_INTERVAL['RQ_SIZE>1'] : RQ_SIZE_gt_1,
}
