import dis, types
import inspect


def wipe_logger(func: types.FunctionType | type) -> types.FunctionType | type:
    from .defaults import ENABLE_LOGGING
    if ENABLE_LOGGING:
        return func

    if inspect.isclass(func):
        for k, v in func.__dict__.items():
            if inspect.isfunction(v):
                setattr(func, k, wipe_logger(v))
            elif type(v) is staticmethod:
                setattr(func, k, staticmethod(wipe_logger(v.__func__)))
        return func

    load_global = dis.opmap['LOAD_GLOBAL']
    nop = dis.opmap['NOP']
    call_method = dis.opmap['CALL_METHOD']

    bytecode = list(func.__code__.co_code)
    mode = 0
    for n, byte in enumerate(bytecode[::2]):
        op = byte
        i = n * 2
        arg = bytecode[i + 1]
        if mode == 0:
            if op == load_global and func.__code__.co_names[arg] == "logger":
                bytecode[i] = nop
                mode = 1
        elif mode == 1:
            bytecode[i] = nop
            if op == call_method:
                bytecode[i + 2] = nop
                mode = 0

    return types.FunctionType(
        types.CodeType(
            func.__code__.co_argcount,
            func.__code__.co_posonlyargcount,
            func.__code__.co_kwonlyargcount,
            func.__code__.co_nlocals,
            func.__code__.co_stacksize,
            func.__code__.co_flags,
            bytes(bytecode),
            func.__code__.co_consts,
            func.__code__.co_names,
            func.__code__.co_varnames,
            func.__code__.co_filename,
            func.__code__.co_name,
            func.__code__.co_firstlineno,
            func.__code__.co_lnotab,
            func.__code__.co_freevars,
            func.__code__.co_cellvars,
        ),
        func.__globals__,
        func.__name__,
        func.__defaults__,
        func.__closure__,
    )

