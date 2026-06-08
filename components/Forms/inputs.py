from pantra.ctx import *

caption: Property[str] = ''
required: Property[bool] = False
value: Property[str] = ''
error: Property[str] = ''
readonly: Property[bool] = False

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

