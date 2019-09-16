import json
from string import Template

SUBSTITUTE = {
	'EXEC_EVT'    : '0',
	'EXIT_EVT'    : '1',
	'WAKEUP'      : '2',
	'WAKEUP_NEW'  : '3',
	'BLOCK'       : '4',
	'BLOCK_IO'    : '5',
	'BLOCK_LOCK'  : '6',
	'WAKEUP_LOCK' : '7',
	'WAKER_LOCK'  : '8',
	'FORK_EVT'    : '9',
	'TICK_EVT'    : '10',
	'CTX_SWITCH'  : '11',
	'MIGRATE_EVT' : '12',
	'RQ_SIZE'     : '13',
	'IDLE_BALANCE_BEG' : '14',
	'IDLE_BALANCE_END' : '15',
	'PERIODIC_BALANCE_BEG' : '16',
	'PERIODIC_BALANCE_END' : '17',
}

def loads(o, substitute=None, log=print):
	if substitute is None:
		# FUTURE: raise exception
		log(f'WARNING: Please provide substitute. Will use {SUBSTITUTE} instead.')
		substitute = SUBSTITUTE
	d = json.loads(o)
	d = parse(d, **substitute)
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
