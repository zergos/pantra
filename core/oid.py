import ctypes

gen_id = id


def get_object(oid):
    return ctypes.cast(oid, ctypes.py_object).value


