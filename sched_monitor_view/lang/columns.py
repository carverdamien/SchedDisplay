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
def copy(df, key):
	return df[key]
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
def sel_equals(df, a, b):
	return a == b
OPERATOR = {
	'copy' : copy,
	'+'    :  add,
	'first' : first,
	'last' : last,
	'=='   : sel_equals,
}
