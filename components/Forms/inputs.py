from core.ctx import *

caption: str = ''
required: bool = False
value: str = ''
error: str = ''

validators = []


def validate(func, message):
    validators.append((func, message))


def is_valid():
    for f, m in validators:
        if not f():
            ctx.error = m
            return False
    if required and not value:
        ctx.error = f'{caption} field is required'
        return False
    ctx.error = ''
    return True

