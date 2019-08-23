# Do NOT import pandas!
import numpy as np
import operator

# Requirements:
#
# The search returns at most:
# N rows of exactly M positive integers.
# An integer represents the index position
# of the record in dd.
#
# The search engine MUST be in O(N*M)
# Where N is the number of records in the trace
# Where M is the number of records in the pattern
#
# The search must NOT make assumptions on dd.keys
#
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
    keep[:] = apply_set_constraint(merge, constraint)
    results[root_name][keep] = idx[keep]
    return keep

def __set_constaint_op__(op):
    def f(dd, key, value):
        return op(dd[key], value)
    return f


SET_CONSTRAINT_COMPARE = {
    "==":__set_constaint_op__(operator.__eq__),
    "!=":__set_constaint_op__(operator.__ne__),
    "<" :__set_constaint_op__(operator.__lt__),
    ">" :__set_constaint_op__(operator.__gt__),
    "<=":__set_constaint_op__(operator.__le__),
    ">=":__set_constaint_op__(operator.__ge__),
}

SET_CONSTRAINT_LOGICAL = {
    "&" :__set_constaint_op__(operator.__and__),
    "|" :__set_constaint_op__(operator.__or__),
}

SET_CONSTRAINT_OP = {
    **SET_CONSTRAINT_COMPARE,
    **SET_CONSTRAINT_LOGICAL,
}

def apply_set_constraint(dd, constraint):
    # args are read only
    if not isinstance(constraint, list):
        raise Exception("constraint({}) must be a list".format(constraint))
    elif len(constraint) == 0:
        return
    elif constraint[0] not in SET_CONSTRAINT_OP:
        raise Exception("{} is not a valid operator on set. Try:{}".format(
            constraint[0],
            list(SET_CONSTRAINT_OP.keys()),
        ))
    elif len(constraint) == 3:
        op, a, b = constraint
        if op in SET_CONSTRAINT_COMPARE:
            pass
        elif op in SET_CONSTRAINT_LOGICAL:
            a = apply_set_constraint(dd, a)
            b = apply_set_constraint(dd, b)
            pass
        else:
            raise Exception("Oops! op:{} a:{} b:{}".format(op, a, b))
        op = SET_CONSTRAINT_OP[op]
        return op(dd, a,b)
    else:
        raise Exception("Oops! constraint:{}".format(constraint))

def search_node(results, dd, idx, node, root_name, keep):
    # modify results[name]
    # remaining args are read only
    name, constraint = node["name"], node["constraint"]
    results[name][keep] = results[root_name][keep]
    N = len(results[name][keep])
    for i in idx[keep]:
        apply_reduction_constraint(results[name], results, dd, i, constraint)

REDUCTION_CONSTRAINT_OP = {
}

def apply_reduction_constraint(node_results, results, dd, i, constraint):
    # TODO:
    # modify node_results[i]
    # remaining args are read only
    if not isinstance(constraint, list):
        raise Exception("constraint({}) must be a list".format(constraint))
    elif len(constraint) == 0:
        return
    elif constraint[0] not in REDUCTION_CONSTRAINT_OP:
        raise Exception("{} is not a valid reduction operator. Try:{}".format(
            constraint[0],
            list(REDUCTION_CONSTRAINT_OP.keys()),
        ))
    else:
        raise Exception("Oops!")
