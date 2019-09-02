#!/usr/bin/env python3
import sys
from tabulate import tabulate

def main():
	line = sys.stdin.readlines()
	header, line = line[0].split(), line[1:]
	row = []
	for l in line:
		l = l.split()
		row.append(l[0:len(header)-1]+[' '.join(l[len(header)-1:])])
	print(tabulate(row, headers=header))

if __name__ == '__main__':
	main()
