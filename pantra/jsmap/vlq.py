# converted to Python from https://github.com/Rich-Harris/vlq/blob/master/src/vlq.ts

from __future__ import annotations

import typing
if typing.TYPE_CHECKING:
    from typing import *

charToInteger: Dict[str, int] = {}
integerToChar: Dict[int, str] = {}

for i, char in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='):
    charToInteger[char] = i
    integerToChar[i] = char


def decode(string: str) -> List[int]:
    result = []
    shift = 0
    value = 0
    for sym in string:
        integer = charToInteger.get(sym)

        if integer is None:
            raise ValueError(f'Invalid character ({sym})')

        hasContinuationBit = integer & 32
        integer &= 31
        value += integer << shift

        if hasContinuationBit:
            shift += 5
        else:
            shouldNegate = value & 1
            value >>= 1

            if shouldNegate:
                result.append(-0x80000000 if value == 0 else -value)
            else:
                result.append(value)

            # reset
            value = shift = 0

    return result


def encode(value: Union[int, List[int]]) -> str:
    result: str

    if type(value) is int:
        result = encodeInteger(value)
    else:
        result = ''
        for v in value:
            result += encodeInteger(v)
    return result


def encodeInteger(num: int) -> str:
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
