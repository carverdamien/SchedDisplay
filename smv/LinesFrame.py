import pandas as pd
import dask
from multiprocessing import cpu_count

def from_df(df, config):
	df['timestamp'] = df['timestamp']-min(df['timestamp'])
	required = {
		'x0':df['timestamp'],
		'x1':df['timestamp'],
		'y0':df['cpu']+0.,
		'y1':df['cpu']+0.5,
		'c':df['event'],
	}
	extra = ['arg0', 'arg1', 'addr', 'pid']
	required.update({k:df[k] for k in extra if k in df})
	lines = pd.DataFrame(required) # TODO: dask asap
	lines['c'] = lines['c'].astype('category')
	lines = lines[config['shape']]
	lines = dask.dataframe.from_pandas(lines, npartitions=cpu_count())
	lines.persist() # Persist multiple Dask collections into memory
	return lines