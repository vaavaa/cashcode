import json


def get_hash_of_list(v):
    if v is None:
        v = list()
    elif type(v) is not list:
        v = [v]
    return hash(json.dumps(v, sort_keys=True))

def are_lists_equal(v1, v2):
    return get_hash_of_list(v1) == get_hash_of_list(v2)

def to_tuple(v=None):
    if v is None:
        return tuple()
    elif type(v) is tuple:
        return v
    else:
        return (v, )

