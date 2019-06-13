from bokeh.models import ColumnDataSource
from functools import partial
from threading import Thread
from tornado import gen
import h5py, time, os
import numpy as np

@gen.coroutine
def updateSource(source, x0, y0, x1, y1, rollover=None):
    source.stream(
        dict(
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
        ),
        rollover,
    )
    pass

def blocking_task(doc, select, plot, source):
    path = None
    while True:
        # TODO: replace sleep with on_change
        # while path == select.value:
        #     time.sleep(1)
        # path = select.value
        # if not os.path.exists(path):
        #    continue
        path = '/mnt/data/damien/git/profiler/raw/hackbench/monitored/output.hdf5'
        with h5py.File(path) as f:
            dataset = f['sched_monitor']['tracer-raw']
            for cpu in dataset.keys():
                N = len(dataset[cpu]['timestamp'])
                timestamp = np.array(dataset[cpu]['timestamp'])
                event = np.array(dataset[cpu]['event'])
                for i in range(18):
                    sel = event == i
                    x0 = timestamp[sel]
                    x1 = timestamp[sel]
                    y0 = float(cpu) * np.ones(len(x0))
                    y1 = (float(cpu)+.25) * np.ones(len(x0))
                    doc.add_next_tick_callback(
                        partial(
                            updateSource,
                            source=source[i],
                            x0=x0,
                            y0=y0,
                            x1=x1,
                            y1=y1,
                        )
                    )
        break

def Source(doc, select, plot):
    source = [ColumnDataSource(
        data=dict(x0=[], y0=[], x1=[], y1=[])
    ) for i in range(18)]
    thread = Thread(
        target=blocking_task,
        args=(
            doc,
            select,
            plot,
            source,
        )
    )
    thread.start()
    return source
