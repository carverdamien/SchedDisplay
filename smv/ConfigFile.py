import json
from string import Template

def loads(o):
	d = json.loads(o)
	d = parse(d)
	return d

def parse(o, **kwargs):
	if isinstance(o, dict):
		for k in o:
			o[k] = parse(o[k], **kwargs)
	elif isinstance(o, list):
		for i in range(len(o)):
			o[i] = parse(o[i], **kwargs)
	elif isinstance(o, str):
		t = Template(o)
		o = t.substitute(**kwargs)
	else:
		pass
	return o
