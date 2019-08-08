EXT=png
JSON=config.json
HDF5=$(wildcard kbuild_sched/*.hdf5) $(wildcard kbuild_all/*.hdf5)
IMG=$(HDF5:%.hdf5=%.$(EXT))

all:$(IMG)

clean:
	rm -f $(IMG)

%.$(EXT): %.hdf5 $(JSON)
	./export.py $@ $^
