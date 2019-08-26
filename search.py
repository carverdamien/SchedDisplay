#!/usr/bin/env python3
from smv.SearchEngine import search
import smv.DataDict as DataDict
import sys
import numpy as np
import pandas as pd

def main():
    _, tar, out, pattern = sys.argv
    pattern = [
        {
            "name" : "a",
            "constraint" : []
        },
        {
            "name" : "b",
            "constraint":
            [
                "argmin",
                "timestamp",
                [
                    "&", 
                    [
                        "&",
                        ["==","cpu",["get","cpu","a"]],
                        ["==","event",["get","event","a"]],
                    ],
                    [">","timestamp",["get","timestamp","a"]]
                ]
            ]
        },
    ]
    dd = DataDict.from_tar(tar)
    N = 100000 * 2 * 2
    N = min(len(dd['timestamp']),N)
    dd = {k:dd[k][0:N] for k in dd if k in ['timestamp','event','cpu']}
    # dd['timestamp'] = np.sort(dd['timestamp'])
    dd['timestamp'] -= dd['timestamp'][0]
    # dd['timestamp'] -= min(dd['timestamp'])
    result = search(dd, pattern)
    new = dd['timestamp'][result["b"]]
    from compute_nxt_of_same_evt_on_same_cpu import parallel_nxt_of_same_evt_on_same_cpu
    old = parallel_nxt_of_same_evt_on_same_cpu(dd, 'timestamp')
    sel = new != old
    n = len(new[sel])
    if n != 0:
        print(pd.DataFrame(dict(new=new,old=old,b=result['b'],**dd)))
        print('len !=',n)
    print(N)
    pass

if __name__ == "__main__":
    main()
