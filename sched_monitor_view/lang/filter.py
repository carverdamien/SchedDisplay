import numpy as np

def sel(df, expression):
	if len(expression) == 0:
		return np.ones(len(df),dtype=bool)
	op = expression[0]
	args = expression[1:]
	for i in range(len(args)):
		if isinstance(args[i], list):
			args[i] = sel(df, args[i])
	return OPERATOR[op](df, *args)
def key_equals_value(df, key, val):
	return df[key] == val
def key_not_equals_value(df, key, val):
	return df[key] != val
def key_gt_value(df, key, val):
	return df[key] > val
def a_and_b(df, a, b):
	return a & b
def a_or_b(df, a, b):
	return a | b
OPERATOR = {
	'==' : key_equals_value,
	'!=' : key_not_equals_value,
	'>'  : key_gt_value,
	'&'  : a_and_b,
	'|'  : a_or_b,
}
