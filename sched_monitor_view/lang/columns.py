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
OPERATOR = {
	'copy' : copy,
	'+'    :  add,
}
