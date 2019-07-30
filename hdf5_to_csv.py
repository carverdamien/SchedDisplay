#!/usr/bin/env python3
from sched_monitor_view.bg.loadDataFrame import fg

def main():
	import sys
	csv, hdf5 = sys.argv[1:3]
	def done(*args,**kwargs):
		pass
	def callback(path, data, done):
		data['df'].to_csv(csv)
		pass
	fg(hdf5, 0, callback, done)
	pass

if __name__ == '__main__':
	main()