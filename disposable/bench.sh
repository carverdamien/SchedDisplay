#!/bin/bash
set -e
exec >> $0
echo ${HOSTNAME}:$(date)
perf stat -e cycles,instructions,cache-misses -- python3 ./disposable/bench.py 2>&1
exit 0
dc-Latitude-7390:mercredi 18 septembre 2019, 15:17:16 (UTC+0200)
data/sched_monitor/tracer-raw/df/event.npz loaded in 0.8863976001739502 s
data/sched_monitor/tracer-raw/df/cpu.npz loaded in 1.1873736381530762 s
data/sched_monitor/tracer-raw/df/timestamp.npz loaded in 1.567845344543457 s

 Performance counter stats for 'python3 ./disposable/bench.py':

   173 719 355 962      cycles                                                      
    79 096 899 657      instructions              #    0,46  insns per cycle        
     3 105 438 439      cache-misses                                                

      20,401038102 seconds time elapsed

dc-Latitude-7390:mercredi 18 septembre 2019, 15:17:36 (UTC+0200)
data/sched_monitor/tracer-raw/df/event.npz loaded in 0.9571607112884521 s
data/sched_monitor/tracer-raw/df/cpu.npz loaded in 1.2551994323730469 s
data/sched_monitor/tracer-raw/df/timestamp.npz loaded in 1.5439460277557373 s

 Performance counter stats for 'python3 ./disposable/bench.py':

   179 970 382 948      cycles                                                      
    79 158 822 345      instructions              #    0,44  insns per cycle        
     3 087 851 236      cache-misses                                                

      20,403115297 seconds time elapsed

dc-Latitude-7390:mercredi 18 septembre 2019, 15:17:57 (UTC+0200)
data/sched_monitor/tracer-raw/df/event.npz loaded in 0.8991670608520508 s
data/sched_monitor/tracer-raw/df/cpu.npz loaded in 1.2476956844329834 s
data/sched_monitor/tracer-raw/df/timestamp.npz loaded in 1.5977113246917725 s

 Performance counter stats for 'python3 ./disposable/bench.py':

   175 492 057 093      cycles                                                      
    78 958 917 448      instructions              #    0,45  insns per cycle        
     3 102 604 492      cache-misses                                                

      20,459245871 seconds time elapsed

i44:Wed Sep 18 18:16:47 CEST 2019
/usr/local/lib/python3.7/site-packages/datashader/transfer_functions.py:21: FutureWarning: xarray subclass Image should explicitly define __slots__
  class Image(xr.DataArray):
data/sched_monitor/tracer-raw/df/event.npz loaded in 1.560256004333496 s
data/sched_monitor/tracer-raw/df/cpu.npz loaded in 2.0440268516540527 s
data/sched_monitor/tracer-raw/df/timestamp.npz loaded in 2.6061675548553467 s

 Performance counter stats for 'python3 ./disposable/bench.py':

    68,206,607,366      cycles:u                                                    
    81,808,484,992      instructions:u            #    1.20  insn per cycle         
       994,907,473      cache-misses:u                                              

      22.591915869 seconds time elapsed

      30.276258000 seconds user
      41.398438000 seconds sys


amd48b-systeme:Wed Sep 18 18:36:43 CEST 2019
/usr/local/lib/python3.7/site-packages/datashader/transfer_functions.py:21: FutureWarning: xarray subclass Image should explicitly define __slots__
  class Image(xr.DataArray):
data/sched_monitor/tracer-raw/df/event.npz loaded in 3.7294673919677734 s
data/sched_monitor/tracer-raw/df/cpu.npz loaded in 4.310714483261108 s
data/sched_monitor/tracer-raw/df/timestamp.npz loaded in 5.075737237930298 s

 Performance counter stats for 'python3 ./disposable/bench.py':

   422,875,628,149      cycles                                                      
   103,802,666,365      instructions              #    0.25  insn per cycle                                            
     3,162,277,809      cache-misses                                                

      66.617749421 seconds time elapsed

