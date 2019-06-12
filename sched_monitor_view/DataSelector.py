from functools import partial
from bokeh.models.widgets import Select
from threading import Thread
from tornado import gen
import os

import time

def find_hdf5():
    ROOT = '/mnt/data/damien/git/profiler/raw/hackbench/monitored'
    for root, dirs, files in os.walk(ROOT, topdown=False):
        for name in files:
            path = os.path.join(root, name)
            if '.hdf5' == os.path.splitext(name)[1]:
                yield path

@gen.coroutine
def updateDataSelector(s, options):
    s.options = options

def blocking_task(doc, s):
    while True:
        # TODO: replace sleep with ionotify
        time.sleep(1)
        options = list(find_hdf5())
        doc.add_next_tick_callback(partial(updateDataSelector, s=s, options=options))

def DataSelector(doc):
    s = Select(
        title='Data:'
    )
    thread = Thread(target=blocking_task, args=(doc,s))
    thread.start()
    return s
