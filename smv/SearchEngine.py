# Do NOT import pandas!
import numpy as np
import operator
import time

try:
    from tqdm import tqdm
except Exception as e:
    def tqdm(X):
        for x in X:
            yield x

def log(func):
    def f(*args, **kwargs):
        start = time.time()
        #print('{}({}) starts at {}'.format(func.__name__, str(args), start))
        r = func(*args, **kwargs)
        end = time.time()
        #print('{}({}) took {} s'.format(func.__name__, str(args), end - start))
        print('{} took {} s'.format(func.__name__, end - start))
        return r
    return f

# Requirements:
#
# The search returns at most:
# N rows of exactly M positive integers.
# An integer represents the index position
# of the record in dd.
#
# The search engine MUST be in O(N*M) (Right now its not)
# Where N is the number of records in the trace
# Where M is the number of records in the pattern
#
# The search must NOT make assumptions on dd.keys
#
@log
def search(dd, pattern, dependency=None):
    N = len(dd[next(iter(dd.keys()))])
    M = len(pattern)
    name = [p['name'] for p in pattern]
    for n in name:
        if n in dd:
            raise Exception('Name Collision: cannot use {} as name'.format(n))
    # Alloc
    idx = np.arange(N)
    keep = np.ones(N,dtype=bool)
    results = {
        n : np.empty(N,dtype=int)
        for n in name
    }
    # Init -1
    for r in results.values():
        r[:]=-1
    root = pattern[0]
    search_root(results, keep, dd, idx, root)
    SET_CONSTRAINT_OP.update(SET_CONSTRAINT_OP_AFTER_ROOT)
    # Search sequentially
    # TODO: use a dependency graph for parallel search
    if len(pattern) > 1:
        for node in pattern[1:]:
            search_node(results, dd, idx, node, root['name'], keep)
    # Drop -1
    # TODO: @parallel
    for r in results.values():
        keep = keep & (r != -1)
    # TODO: @parallel
    for k in results:
        results[k] = results[k][keep]
    return results

def search_root(results, keep, dd, idx, root):
    # modify results[root_name]
    # remaining args are read only
    root_name, constraint = root["name"], root["constraint"]
    merge = {**results, **dd}
    keep[:] = apply_set_constraint(merge, constraint, set_nop=keep)
    results[root_name][keep] = idx[keep]
    return keep

CACHE_UNORDERED = {}
def cache_unordered(k,op,A,b):
    if k not in CACHE_UNORDERED:
        print('CACHING UNORDERED {}'.format(k))
        CACHE_UNORDERED[k] = op(A,b)
    return CACHE_UNORDERED[k]

def inverse(a,i):
    return a[i]

def cut(a,i,N):
    if i == 0:
        a[:] = True
    elif i == N:
        a[:] = False
    else:
        a[:i] = False
        a[i:] = True

# CACHE_ORDERED = {}
# def cache_ordered(k,op,A,b):
#     N = len(A)
#     if k not in CACHE_ORDERED:
#         print('CACHING ORDERED {}'.format(k))
#         argsort = np.argsort(A)
#         inverse_argsort = np.arange(len(A))[argsort]
#         sort = A[argsort]
#         private = np.empty(N, dtype=bool)
#         CACHE_ORDERED[k] = argsort, inverse_argsort, sort, private
#     else:
#         argsort, inverse_argsort, sort, private = CACHE_ORDERED[k]
#     if op in [operator.__ge__, operator.__lt__, operator.__le__]:
#         raise Exception('TODO')
#     elif op in [operator.__gt__]:
#         i = np.searchsorted(sort, b, side='right')
#         cut(private,i,N)
#         # inverse takes too much time
#         return inverse(private,inverse_argsort)
#     else:
#         raise Exception('Ooops!')

CACHE_ORDERED = {}
def cache_ordered(k,op,A,b):
    N = len(A)
    if k not in CACHE_ORDERED:
        print('CACHING ORDERED {}'.format(k))
        is_sorted = np.sum(~(np.diff(A) >= 0)) == 0
        private = np.empty(N, dtype=bool)
        if not is_sorted:
            print('ordered operation on unsorted array')
            raise Exception('ordered operation on unsorted array')
        CACHE_ORDERED[k] = is_sorted, private
    else:
        is_sorted, private = CACHE_ORDERED[k]
    if op in [operator.__ge__, operator.__lt__, operator.__le__]:
        raise Exception('TODO')
    elif op in [operator.__gt__]:
        i = np.searchsorted(A, b, side='right')
        cut(private,i,N)
        return private
    else:
        raise Exception('Ooops!')

def __set_constaint_op__(op):
    def f(dd, a, b, row=None):
        # Slowest part! maybe when op == __and__?
        if isinstance(a, str) and not isinstance(b, str):
            if f in SET_CONSTRAINT_COMPARE_UNORDERED.values():
                # CACHE ME
                k = "{}{}{}".format(op,a,b)
                return cache_unordered(k,op,dd[a],b)
            elif f in SET_CONSTRAINT_COMPARE_ORDERED.values():
                # SORT ME
                k = a
                return cache_ordered(k,op,dd[a],b)
            else:
                print(op)
                raise Exception('Ooops!')
        elif not isinstance(a, str) and isinstance(b, str):
            # CACHE ME
            return op(a, dd[b])
        elif isinstance(a, str) and isinstance(b, str):
            return op(dd[a], dd[b])
        else:
            return op(a,b)
    return f


SET_CONSTRAINT_COMPARE_UNORDERED = {
    "==":__set_constaint_op__(operator.__eq__),
    "!=":__set_constaint_op__(operator.__ne__),
}

SET_CONSTRAINT_COMPARE_ORDERED = {
    "<" :__set_constaint_op__(operator.__lt__),
    ">" :__set_constaint_op__(operator.__gt__),
    "<=":__set_constaint_op__(operator.__le__),
    ">=":__set_constaint_op__(operator.__ge__),
}

SET_CONSTRAINT_COMPARE = {
    **SET_CONSTRAINT_COMPARE_UNORDERED,
    **SET_CONSTRAINT_COMPARE_ORDERED,
}

SET_CONSTRAINT_LOGICAL = {
    "&" :__set_constaint_op__(operator.__and__),
    "|" :__set_constaint_op__(operator.__or__),
}

SET_CONSTRAINT_OP = {
    **SET_CONSTRAINT_COMPARE,
    **SET_CONSTRAINT_LOGICAL,
}

def apply_set_constraint(dd, constraint, row=None, set_nop=None):
    # args are read only
    if not isinstance(constraint, list):
        raise Exception("constraint({}) must be a list".format(constraint))
    elif len(constraint) == 0:
        return set_nop
    elif constraint[0] not in SET_CONSTRAINT_OP:
        raise Exception("{} is not a valid operator on set. Try:{}".format(
            constraint[0],
            list(SET_CONSTRAINT_OP.keys()),
        ))
    elif len(constraint) == 3:
        opname, a, b = constraint
        if isinstance(a, list):
            a = apply_set_constraint(dd, a, row=row, set_nop=set_nop)
        if isinstance(b, list):
            b = apply_set_constraint(dd, b, row=row, set_nop=set_nop)
        if opname in SET_CONSTRAINT_COMPARE:
            return SET_CONSTRAINT_OP[opname](dd, a, b)
        elif opname in SET_CONSTRAINT_LOGICAL:
            return SET_CONSTRAINT_OP[opname](dd, a, b)
        elif opname in SET_CONSTRAINT_OP_AFTER_ROOT:
            return SET_CONSTRAINT_OP[opname](dd, row, a, b)
        else:
            raise Exception("Oops! op:{} a:{} b:{}".format(op, a, b))
    else:
        raise Exception("Oops! constraint:{}".format(constraint))

def search_node(results, dd, idx, node, root_name, keep):
    # modify results[name]
    # remaining args are read only
    name, constraint = node["name"], node["constraint"]
    results[name][keep] = results[root_name][keep]
    N = len(results[name][keep])
    merge = {**results, **dd}
    for i in tqdm(idx[keep]):
        results[name][i] = apply_reduction_constraint(i, idx, merge, constraint, red_nop=results[name][i], set_nop=keep)

def __reduction_contraint_op__(op):
    def f(idx, dd, key, constraint, row=None, red_nop=None, set_nop=None):
        sel = apply_set_constraint(dd, constraint, row=row, set_nop=set_nop)
        set_result = dd[key][sel]
        if len(set_result) == 0:
            return red_nop
        else:
            return idx[sel][op(set_result)]
    return f

def __get__(dd, row, key, var):
    return dd[key][dd[var][row]]

SET_CONSTRAINT_OP_AFTER_ROOT = {
    "get" : __get__,
}

REDUCTION_CONSTRAINT_OP = {
    "argmin":__reduction_contraint_op__(np.argmin),
    "argmax":__reduction_contraint_op__(np.argmax),
}

def apply_reduction_constraint(row, idx, dd, constraint, red_nop=None, set_nop=None):
    # TODO:
    # modify node_results[i]
    # remaining args are read only
    if not isinstance(constraint, list):
        raise Exception("constraint({}) must be a list".format(constraint))
    elif len(constraint) == 0:
        return red_nop
    elif constraint[0] not in REDUCTION_CONSTRAINT_OP:
        raise Exception("{} is not a valid reduction operator. Try:{}".format(
            constraint[0],
            list(REDUCTION_CONSTRAINT_OP.keys()),
        ))
    elif len(constraint) == 3:
        op, key, set_constraint = constraint
        op = REDUCTION_CONSTRAINT_OP[op]
        return op(idx, dd, key, set_constraint, row=row, set_nop=set_nop, red_nop=red_nop)
    else:
        raise Exception("Oops! constraint:{}".format(constraint))
