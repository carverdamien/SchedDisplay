#!/usr/bin/env python3
from smv.SearchEngine import search
import smv.DataDict as DataDict
import sys

def main():
    _, tar, out, pattern = sys.argv
    pattern = [
        {"name":"a","constraint":["==","cpu",0]},
        {"name":"b","constraint":[]},
    ]
    dd = DataDict.from_tar(tar)
    result = search(dd, pattern)
    print(result)
    pass

if __name__ == "__main__":
    main()
