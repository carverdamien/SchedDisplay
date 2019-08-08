#!/usr/bin/env python3
import sys, json
from sched_monitor_view.export import export

if __name__ == '__main__':
	img_path, json_path = sys.argv[1:3]
	with open(json_path) as f:
		export(img_path, json.load(f))
