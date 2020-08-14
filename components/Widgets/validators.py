from pantra.ctx import *

validators = []


def validate(func, message):
    validators.append((func, message))


def check_validators():
    for f, m in validators:
        if not f():
            ctx['error'] = m
            return False
    return True
