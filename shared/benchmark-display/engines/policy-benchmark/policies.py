"""Three fixed JSON acceptance policies. No user code is loaded or executed."""
import json
import math

NAMES = ('python-default-v1', 'reject-constants-v1', 'unique-finite-v1')


def reject_constant(value):
    raise ValueError('nonfinite constant')


def finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('nonfinite float')
    return result


def unique_members(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('duplicate object member')
        result[name] = value
    return result


def accepts(name, text):
    if name not in NAMES:
        raise ValueError('unknown fixed policy')
    options = {}
    if name != NAMES[0]:
        options['parse_constant'] = reject_constant
    if name == NAMES[2]:
        options.update(object_pairs_hook=unique_members, parse_float=finite_float)
    try:
        json.loads(text, **options)
    except (ValueError, RecursionError):
        return False
    return True
