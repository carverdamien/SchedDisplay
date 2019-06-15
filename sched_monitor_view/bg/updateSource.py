from threading import Thread
import operator
import numpy as np
import Types

def plot(data, truncate, event_selected, interval_selected, tlim, callback):
	args = (data, truncate, event_selected, interval_selected, tlim, callback)
	return Thread(target=target, args=args)

def target(data, truncate, event_selected, interval_selected, tlim, callback):
	source_event_data = []
	source_interval_data = []
	tlim = recompute_tlim(data, truncate, event_selected, interval_selected, tlim)
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
				timestamp = timestamp[sel]
				N = len(timestamp)
				x0 = np.append(x0, timestamp)
				y0 = np.append(y0, (float(cpu)+y_offset) * np.ones(N))
				y1 = np.append(y1, (float(cpu)+.75+y_offset) * np.ones(N))
			y_offset += len(data[path])
		source_event_data.append(dict(x0=x0, y0=y0, x1=x0, y1=y1))
	for i in range(len(Types.INTERVAL)):
		if i not in interval_selected or i not in HANDLER:
			source_interval_data.append(dict(x0=[], y0=[], x1=[], y1=[]))
			continue
		source_interval_data.append(HANDLER[i](data, tlim))
	callback(source_event_data, source_interval_data, tlim)

def recompute_tlim(data, truncate, event_selected, interval_selected, tlim):
	for event_id in range(len(Types.EVENT)):
		if event_id not in event_selected:
			continue
		for path in data:
			for cpu in data[path]:
				timestamp = data[path][cpu]['timestamp']
				event = data[path][cpu]['event']
				# todo: searchsorted
				sel = (event == event_id) & (timestamp >= tlim[0]) & (timestamp <= tlim[1])
				if len(timestamp[sel]) <= truncate:
					continue
				timestamp = timestamp[sel][:truncate]
				tlim = (tlim[0], min(max(timestamp), tlim[1]))
	for i in range(len(Types.INTERVAL)):
		if i not in interval_selected or i not in HANDLER:
			continue
		tlim = RECOMPUTE_TLIM_HANDLER[i](data, truncate, tlim)
	return tlim

def recompute_tlim_interval(data, truncate, tlim, event_id, measurement, op, value):
	tmax = max([
		timestamp[-1]
		for dict_of_cpu in data.values()
		for dict_of_record in dict_of_cpu.values()
		for timestamp in [dict_of_record['timestamp']]
		if len(timestamp) > 0
	]+[0])
	for path in data:
		for cpu in data[path]:
			timestamp = data[path][cpu]['timestamp']
			event = data[path][cpu]['event']
			# todo: searchsorted
			sel_event = (event == event_id)
			timestamp = timestamp[sel_event]
			m = data[path][cpu][measurement][sel_event]
			sel_x0 = op(m, value)
			sel_x1 = np.append([False], sel_x0)
			if np.sum(sel_x0) == 0:
				continue
			x0 = timestamp[sel_x0]
			x1 = np.append(timestamp, [tmax])[sel_x1]
			sel_tlim = intersection(x0, x1, tlim)
			x0 = x0[sel_tlim]
			x1 = x1[sel_tlim]
			while len(x0) > truncate:
				tlim1 = min([max(x0[((x0 >= tlim[0]) & (x0 <= tlim[1]))]), max(x1[((x1 >= tlim[0]) & (x1 <= tlim[1]))])])
				tlim = (tlim[0], tlim1-1)
				# tlim = (tlim[0], tlim[0] + (tlim[1]-tlim[0])/2)
				sel_tlim = intersection(x0, x1, tlim)
				x0 = x0[sel_tlim]
				x1 = x1[sel_tlim]
	return tlim

def RQ_SIZE_eq_0_RECOMPUTE_TLIM(data, truncate, tlim):
	return recompute_tlim_interval(data, truncate, tlim, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.eq, 0)
def RQ_SIZE_gt_0_RECOMPUTE_TLIM(data, truncate, tlim):
	return recompute_tlim_interval(data, truncate, tlim, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.gt, 0)
def RQ_SIZE_eq_1_RECOMPUTE_TLIM(data, truncate, tlim):
	return recompute_tlim_interval(data, truncate, tlim, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.eq, 1)
def RQ_SIZE_gt_1_RECOMPUTE_TLIM(data, truncate, tlim):
	return recompute_tlim_interval(data, truncate, tlim, Types.ID_EVENT['RQ_SIZE'], 'arg0', operator.gt, 1)

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
	tmax = max([
		timestamp[-1]
		for dict_of_cpu in data.values()
		for dict_of_record in dict_of_cpu.values()
		for timestamp in [dict_of_record['timestamp']]
		if len(timestamp) > 0
	]+[0])
	y_offset = 0
	for path in data:
		for cpu in data[path]:
			timestamp = data[path][cpu]['timestamp']
			event = data[path][cpu]['event']			
			# todo: searchsorted
			sel_event = (event == event_id)
			timestamp = timestamp[sel_event]
			m = data[path][cpu][measurement][sel_event]
			_r = interval_per_cpu(float(cpu)+y_offset, timestamp, tlim, tmax, m, op, value)
			for k in r:
				r[k] = np.append(r[k], _r[k])
		y_offset+=len(data[path])
	return r

def interval_per_cpu(y_offset, timestamp, tlim, tmax, measurement, op, value):
	sel_x0 = op(measurement, value)
	sel_x1 = np.append([False], sel_x0)
	if np.sum(sel_x0) == 0:
		return dict(x0=[], y0=[], x1=[], y1=[])
	x0 = timestamp[sel_x0]
	x1 = np.append(timestamp, [tmax])[sel_x1]
	sel_tlim = intersection(x0, x1, tlim)
	x0 = x0[sel_tlim]
	x1 = x1[sel_tlim]
	N = len(x0)
	y0 = y_offset * np.ones(N)
	y1 = y_offset * np.ones(N)
	return dict(x0=x0, y0=y0, x1=x1, y1=y1)

def intersection(x0, x1, tlim):
	return ((x0 >= tlim[0]) & (x0 <= tlim[1])) | ((x1 >= tlim[0]) & (x1 <= tlim[1])) | ((x0<tlim[0]) & (x1>tlim[1]))

HANDLER = {
	Types.ID_INTERVAL['RQ_SIZE=0'] : RQ_SIZE_eq_0,
	Types.ID_INTERVAL['RQ_SIZE>0'] : RQ_SIZE_gt_0,
	Types.ID_INTERVAL['RQ_SIZE=1'] : RQ_SIZE_eq_1,
	Types.ID_INTERVAL['RQ_SIZE>1'] : RQ_SIZE_gt_1,
}
RECOMPUTE_TLIM_HANDLER = {
	Types.ID_INTERVAL['RQ_SIZE=0'] : RQ_SIZE_eq_0_RECOMPUTE_TLIM,
	Types.ID_INTERVAL['RQ_SIZE>0'] : RQ_SIZE_gt_0_RECOMPUTE_TLIM,
	Types.ID_INTERVAL['RQ_SIZE=1'] : RQ_SIZE_eq_1_RECOMPUTE_TLIM,
	Types.ID_INTERVAL['RQ_SIZE>1'] : RQ_SIZE_gt_1_RECOMPUTE_TLIM,
}
