# converted to Python from https://github.com/Rich-Harris/vlq/blob/master/src/vlq.ts

from __future__ import annotations

import typing
if typing.TYPE_CHECKING:
    from typing import *

integerToChar: str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
charToInteger: Dict[str, int] = {char: i for i, char in enumerate(integerToChar)}

def decode(string: str) -> List[int]:
    result = []
    shift = 0
    value = 0
    for sym in string:
        integer = charToInteger.get(sym)

        if integer is None:
            raise ValueError(f'Invalid character ({sym})')

        integer &= 31
        value += integer << shift

        if integer & 32:
            shift += 5
        else:
            value >>= 1

            if value & 1:
                result.append(-0x80000000 if value == 0 else -value)
            else:
                result.append(value)

            # reset
            value = shift = 0

    return result


def encode(value: Union[int, List[int]]) -> str:
    result: str

    if type(value) is int:
        result = encode_integer(value)
    else:
        result = ''.join(encode_integer(v) for v in value)
    return result


def encode_integer(num: int) -> str:
    result = ''

    if num < 0:
        num = (-num << 1) | 1
    else:
        num <<= 1

    while True:
        clamped = num & 31
        num >>= 5

        if num > 0:
            clamped |= 32

        result += integerToChar[clamped]
        if num == 0:
            break

    return result
