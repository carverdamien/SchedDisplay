# SchedDisplay

SchedDisplay is a visualization tool for [SchedLog](https://github.com/carverdamien/SchedLog), a custom ring buffer collecting scheduling events in the Linux kernel.

(Note that SchedDisplay is currently being rewritten into [TraceDisplay](https://github.com/carverdamien/trace-cmd), a visualization tool for trace-cmd records.)

[![example](https://github.com/carverdamien/SchedDisplay/raw/master/docs/example.png)](https://github.com/carverdamien/SchedDisplay/raw/master/docs/example.png)

## SchedDisplay in a few Steps

1) Build and launch the webserver with `./docker` script.
2) Open the web app http://localhost:5006/v0.
3) Select a tarball file which contains the data recorded during an experiment and then click select. (see [below](#tarball) for record/import)
4) Select a json file which contains the instructions on how to build the lines in the image from the recorded data and then click select. Uploading a local json file is also supported. (see [below](#json) for writing custom instructions)
5) Select Figure to view the image.

There are additional tabs in the application.
The Console tab reports progress and errors.
The Stat tab computes statistics. 
The Var tab shows available events in the SchedLog kernel.

A jupyter environment is also available https://localhost (the ssl certificate is generated by `jupyter-notebook.sh`).
The token can be obtain by running `docker exec -ti NAME_OF_SCHEDDISPLAY_CONTAINER jupyter notebook list`.
Feel free to duplicate and modify [./examples/notebook/jupyter-example.ipynb](./examples/notebook/jupyter-example.ipynb).

## The tarball record

You can try SchedDisplay with the trace provided in [./examples/trace/kbuild-sched-example.tar](./examples/trace/kbuild-sched-example.tar).
To record your own trace, follow these instructions:
1) install the [SchedLog](https://github.com/carverdamien/SchedLog) kernel.
2) record your experiment with the [sched_log](https://github.com/carverdamien/SchedLog/blob/SchedLog/tools/sched_log/sched_log) script.
3) convert the per-cpu buffers into compressed numpy arrays with the [report.py](https://github.com/carverdamien/RecordSchedLog/blob/master/monitoring/SchedLog/report.py) script.
4) create the tarball and store it in `./examples/trace`

A tarball must at least contain the following files:

* sched_log_traced_events.start (a copy of `/proc/sched_log_traced_events`) which contains the mapping `EVENT_ID -> EVENT_NAME`.
* timestamp.npz
* pid.npz
* event.npz
* cpu.npz
* arg1.npz
* arg0.npz

Check [RecordSchedLog](https://github.com/carverdamien/RecordSchedLog) to discover how we automate our experiments.

## The json instructions

The `input` field lists the data required to build the image.
Some data are directly recorded through SchedLog (timestamp, cpu, event, pid, arg0, arg1).
Other data must be computed.

The `output` field lists the data to store in the image.
Some data are mandatory (x0,y0,x1,y1,c).

The `c` field lists instructions on how to build categories of lines.
For example, the following category draws small vertical lines when the frequency measured at a scheduling tick is between 1.2 and 1.7 GHz on a given CPU.
```
{
        "label" : "[1.2, 1.7] GHz",
        "color" : "#8ded6d",
        "concatenate" : [[
                ["query","event==$TICK & arg1>1200000 & arg1<=1700000"],
                ["=","x0","timestamp"],
                ["=","x1","timestamp"],
                ["=","y0",["+","cpu",0.0]],
                ["=","y1",["+","cpu",0.5]]
        ]]
},
```
See [examples/line/freq4_new.json](examples/line/freq4_new.json) for a full example.
