import json

STATE = {
	'hdf5' : [],
}
def from_json(new_state):
	new_state = json.loads(new_state)
	STATE.clear()
	STATE.update(new_state)
def to_json():
	return json.dumps(STATE)
def is_valid(new_state):
	try:
		return not to_json() == json.dumps(json.loads(new_state))
	except json.decoder.JSONDecodeError as e:
		pass
	return False
def hdf5_is_loaded(path):
	return path in STATE['hdf5']
def load_hdf5(path):
	STATE['hdf5'].append(path)
def unload_hdf5(path):
	STATE['hdf5'].remove(path)
