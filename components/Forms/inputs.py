from pantra.ctx import *

caption: str = ''
required: bool = False
value: str = ''
error: str = ''
readonly: bool = False

validators = []


def validate(func, message):
    validators.append((func, message))


def is_valid():
    for f, m in validators:
        if not f():
            ctx['error'] = m
            return False
    if required and not value:
        ctx['error'] = _('field is required')
        return False
    ctx['error'] = ''
    return True

