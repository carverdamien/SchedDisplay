import numpy as np
import bokeh as bk
import bokeh.plotting as bkplt
import h5py

def main():
    path = './data/not_idle_intervals/linux.hdf5'
    def handleData(data):
        TMIN = min(data[i][0][0] for i in range(len(data)))
        TMAX = max(data[i][1][-1] for i in range(len(data)))
        TWIDTHMAX = TMAX-TMIN
        TWIDTHMIN = min(np.min(data[i][1] - data[i][0]) for i in range(len(data)))
        slider_tmin = bk.models.widgets.Slider(
            title="tmin",
            value=TMIN,
            start=TMIN,
            end=TMAX,
            step=1,
        )
        slider_twidth = bk.models.widgets.Slider(
            title="twidth",
            value=TWIDTHMAX,
            start=TWIDTHMIN,
            end=TWIDTHMAX,
            step=1,
        )
        button_plot = bk.models.widgets.Button(
            label="Plot",
            button_type="success",
        )
        plot = bkplt.figure(
            plot_height=540,
            plot_width=960,
            title=path,
            tools="xpan,reset,save,xwheel_zoom",
            active_scroll='xwheel_zoom',
            y_range=[0, len(data)]
        )
        source = bk.models.ColumnDataSource(data=dict(x=[], y=[]))
        def update_source():
            x, y = [], []
            twidth = slider_twidth.value
            tmin = slider_tmin.value
            tmax = tmin + twidth
            for l in range(len(data)):
                inf, sup = data[l]
                itmin, itmax = np.searchsorted(inf, tmin), np.searchsorted(sup, tmax)
                if itmin == itmax:
                    # No intervals
                    continue
                for i in range(itmin, itmax):
                    x.extend([data[l][0][i], data[l][1][i], float('Nan')])
                    y.extend([l,l, float('Nan')])
            source.data = dict(x=x, y=y)
            print('update_source done')
            pass
        def on_change(name, old, new):
            update_source()
        def on_click(new):
            update_source()
        button_plot.on_click(update_source)
        # for widget in [slider_tmin, slider_twidth]:
        #    widget.on_change('value', update_source)
        text = """Use tmin and twidth to reduce the dataset if the computation is too long"""
        paragraph_explain_tmin_twidth = bk.models.widgets.Paragraph(text=text)
        interactivity = bk.layouts.column(
            paragraph_explain_tmin_twidth,
            slider_tmin,
            slider_twidth,
            button_plot,
        )
        plot.line(
            'x',
            'y',
            source=source,
            line_width=3,
        )
        root = bk.layouts.row(
            interactivity,
            plot,
        )
        bk.io.curdoc().add_root(root)
    loadData(path, handleData)
    pass

def checkData(data):
    for i in range(len(data)):
        print('Checking Data {}'.format(i))
        inf, sup = data[i]
        # inf <= sup
        assert(np.sum(sup < inf) == 0)
        # inf is sorted (inf[i] <= inf[i+1])
        assert(np.sum(np.diff(inf) < 0) == 0)
        # sup is sorted (sup[i] <= sup[i+1])
        assert(np.sum(np.diff(sup) < 0) == 0)
        # sup[i] <= inf[i+1]
        assert(np.sum(inf[1:] < sup[:-1]) == 0)
        pass

def loadData(path, handle):
    with h5py.File(path, 'r') as h:
        data = [np.array(h[cpu]) for cpu in sorted(list(h.keys()), key=lambda e:int(e))]
        checkData(data)
        handle(data)
main()
