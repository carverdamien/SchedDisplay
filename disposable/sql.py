from pandasql import sqldf, load_meat, load_births
pysqldf = lambda q: sqldf(q, globals())
meats = load_meat()
births = load_births()

meats['idx'] = meats.index
births['idx'] = births.index

q = """SELECT
        m.idx as midx, b.idx as bidx
     FROM
        meats m
     INNER JOIN
        births b
           ON m.date = b.date;"""

print(pysqldf(q).head())

import pandas as pd
import numpy as np
EXEC=0
EXIT=1
WAKEUP=2
BLOCK=4
TICK=10
ENQ=13
def dummy_data():
	event = [
		EXEC,
		TICK,
		BLOCK,
		WAKEUP,
		TICK,
		EXIT,
	]
	N = len(event)
	arg1 = [np.NaN if event[i] != TICK else i for i in range(N)]
	# return {
	# 	'cpu'       : np.array([0]*N),
	# 	'event'     : np.array(event),
	# 	'arg1'      : np.array(arg1)
	# }
	return {
		'pid'       : np.array([0]*N+[1]*N),
		'event'     : np.array(event+event),
		'arg1'      : np.array(arg1+arg1)
	}
def dummy_data():
	N = 10000
	tmax = 1000000000
	nr_pid = 2
	nr_cpu = 160
	nr_event = 20
	timestamp = np.random.randint(0,tmax,N).astype(float)
	cpu = np.random.randint(0,nr_cpu,N).astype(float)
	event = np.random.randint(0,nr_event,N)
	pid = np.random.randint(0,nr_pid,N)
	return {
		'timestamp':timestamp,
		'cpu':cpu,
		'event':event,
		'pid':pid,
	}
data = dummy_data()
df = pd.DataFrame(data)
df['idx'] = df.index
print(df)
q = "SELECT e0.idx as e0idx, e1.idx as e1idx FROM (SELECT * FROM df where event=0) as e0 INNER JOIN (SELECT * FROM df where event=1) as e1 ON e0.pid = e1.pid and e0.timestamp <= e1.timestamp;"
print(pysqldf(q).head())


