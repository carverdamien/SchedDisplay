import collections
class FunctionAsDict(collections.Mapping):
    def __init__(self, func):
        super(FunctionAsDict, self).__init__()
        self.func = func
    def __getitem__(self, key):
        return self.func(key)
    def __len__(self, key):
        return 0
    def __iter__(self, key):
        raise StopIteration()
