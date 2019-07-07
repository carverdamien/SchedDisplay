import numpy as np

def compute(df, expression):
	if len(expression) == 0:
		return np.empty(len(df),dtype=bool)
	op = expression[0]
	args = expression[1:]
	for i in range(len(args)):
		if isinstance(args[i], list):
			args[i] = compute(df, args[i])
	return OPERATOR[op](df, *args)
def zeros(df):
	return np.zeros(len(df))
def copy(df, key):
	return np.array(df[key])
def add(df, a, b):
	return a + b
def last(df, sel, i):
	t = np.array(sel)
	idx = np.arange(len(t))[sel]
	# Sets first elements to False
	# Keeps last elements to True
	t[idx[0:i]] = False
	return t
def first(df, sel, i):
	t = np.array(sel)
	idx = np.arange(len(t))[sel]
	# Sets last elements to False
	# Keeps first elements to True
	t[idx[-1:-i-1:-1]] = False
	return t
def key_equals_value(df, key, val):
	return df[key] == val
def a_and_b(df, a, b):
	return a & b
def move(df, a, dst, src):
	a[dst] = a[src]
	return a
def nxt_of_same_evt_on_same_cpu(df, key):
	nxt = copy(df, key)
	events = np.unique(df['event'])
	cpus = np.unique(df['cpu'])
	# Compute == once only
	sel_evt = { evt : df['event'] == evt for evt in events}
	sel_cpu = { cpu :   df['cpu'] == cpu for cpu in cpus}
	for evt in events:
		for cpu in cpus:
			sel = (sel_evt[evt]) & (sel_cpu[cpu])
			f   = first(df, sel, 1)
			l   = last(df, sel, 1)
			nxt = move(df, nxt, f, l)
	return nxt
def diff_of_same_evt(df, key):
	val = np.array(df[key])
	diff = zeros(df)
	events = np.unique(df['event'])
	for evt in events:
		sel = df['event'] == evt
		f = first(df, sel, 1)
		l = last(df, sel, 1)
		diff[f] = val[l] - val[f]
	return diff
OPERATOR = {
	'copy' : copy,
	'+'    :  add,
	'first' : first,
	'last' : last,
	'=='   : key_equals_value,
	'mv'  : move,
	'&'  : a_and_b,
	'nxt_of_same_evt_on_same_cpu' : nxt_of_same_evt_on_same_cpu,
	'diff_of_same_evt' : diff_of_same_evt,
}
