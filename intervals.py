import numpy as np
import bokeh as bk
import bokeh.plotting as bkplt
import h5py

def main():
    path = './data/idle_intervals/linux.hdf5'
    def handleData(data):
        tmin = min(data[i][0][0] for i in range(len(data)))
        tmax = max(data[i][1][-1] for i in range(len(data)))
        slider_t0 = bk.models.widgets.Slider(
            title="t0",
            value=0,
            start=tmin,
            end=tmax,
            step=1
        )
        source = [
            bk.models.ColumnDataSource(data=dict(x=[], y=[]))
            for l in range(len(data))
        ]
        def update_source(attrname, old, new):
            print('TODO')
            pass
        for widget in [slider_t0]:
            widget.on_change('value', update_source)
        interactivity = bk.layouts.column(
            slider_t0,
        )
        plot = bkplt.figure(
            plot_height=540,
            plot_width=960,
            title=path,
            tools="crosshair,pan,reset,save,wheel_zoom",
            x_range=[0, 1],
            y_range=[0, len(data)]
        )
        for src in source:
            plot.line(
                'x',
                'y',
                source=src,
                line_width=3,
                line_alpha=0.6
            )
        root = bk.layouts.row(
            interactivity,
            plot,
        )
        bk.io.curdoc().add_root(root)
    loadData(path, handleData)
    pass

def loadData(path, handle):
    with h5py.File(path, 'r') as h:
        data = [np.array(h[cpu]) for cpu in sorted(list(h.keys()), key=lambda e:int(e))]
        handle(data)

main()
