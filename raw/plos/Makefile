EXT=png
JSON=config.json
HDF5=$(wildcard kbuild_sched/*.hdf5) $(wildcard kbuild_all/*.hdf5)
IMG=$(HDF5:%.hdf5=%.$(EXT))

all:$(IMG) freqdelay.$(EXT) forkwait.$(EXT)

clean:
	rm -f $(IMG)

%.$(EXT): %.hdf5 $(JSON)
	./export.py $@ $^

freqdelay.$(EXT): kbuild_all/320-linux_std.hdf5 freqdelay.json
	./export.py $@ $^

forkwait.$(EXT): kbuild_all/320-linux_std.hdf5 forkwait.json
	./export.py $@ $^
