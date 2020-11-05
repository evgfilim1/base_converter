import re
from math import trunc
from typing import Union, Tuple, Optional

from config import get_config

config = get_config()['core']
NumType = Union[str, int, float]


class ConverterError(Exception):
    pass


class InvalidConversionError(ConverterError):
    def __init__(self, from_base: int, to_base: int, n: str):
        super().__init__(f'Cannot convert number "{n}" from base{from_base} to base{to_base}')


class NumberNotSupportedError(ConverterError):
    def __init__(self, n: str, more_info: str = 'this type of numbers is not supported'):
        super().__init__(f'Cannot convert number "{n}". Reason: {more_info}')


def _check_str(s: NumType) -> bool:
    return _parse_num(s) is not None


def _parse_num(s: NumType) -> Optional[Tuple[str, str, bool]]:
    s = str(s).upper()
    r = re.fullmatch(r'([-+]?)([\dA-Z]+)(?:\.([\dA-Z]+))?', s)
    if r is not None:
        r = r.group(2) or '0', '0.' + (r.group(3) or '0'), r.group(1) == '-'
    return r


def _make_num(a: NumType, b: NumType, negative: bool) -> str:
    a, b = str(a), str(b)
    if a == '':
        a = '0'
    if b.startswith('0.'):
        b = b[2:]
    if config.getboolean('strip_zeros'):
        b = b.rstrip('0')
    if not b:
        result = a
    else:
        result = f'{a}.{b}'
    return ('-' if negative else '') + result


def _letter_to_number(n: str) -> int:
    n = n.upper()
    if n.isdecimal():
        return int(n)
    else:
        return ord(n) - ord('A') + 10


def _number_to_letter(n: int) -> str:
    if n > 9:
        return chr(ord('A') + (n - 10))
    return str(n)


def _int_to_base10(from_base: int, n: str) -> int:
    s = 0
    i = 1
    for c in reversed(n):
        t = _letter_to_number(c)
        if t >= from_base:
            raise InvalidConversionError(from_base=from_base, to_base=10, n=n)
        s += t * i
        i *= from_base
    return s


def _int_from_base10(to_base: int, n: Union[str, int]) -> str:
    res = ''
    if isinstance(n, str) and not n.isdecimal():
        raise InvalidConversionError(from_base=10, to_base=to_base, n=n)
    n = int(n)
    while n != 0:
        res += _number_to_letter(n % to_base)
        n //= to_base
    return res[::-1]


def _float_to_base10(from_base: int, n: str, accuracy: int = 6) -> str:
    s = 0
    i = 1 / from_base
    for c in _parse_num(n)[1][2:]:
        t = _letter_to_number(c)
        if t >= from_base:
            raise InvalidConversionError(from_base=from_base, to_base=10, n=n)
        s += t * i
        i /= from_base
    s = round(s, accuracy)
    if accuracy == 0:
        accuracy = 1
    return format(s, f'.{accuracy}f')


def _float_from_base10(to_base: int, n: Union[str, float], accuracy: int = 6) -> str:
    if isinstance(n, str):
        try:
            n = float(_parse_num(n)[1])
        except ValueError:
            raise InvalidConversionError(from_base=10, to_base=to_base, n=n)
    else:
        n -= trunc(n)
    r = []
    ans = ''
    for _ in range(accuracy + 1):
        n = round(n * to_base, accuracy)
        r.append(trunc(n))
        if n.is_integer():
            break
        n -= trunc(n)
        n = round(n, accuracy)
    round_ = len(r) > accuracy
    m = 0
    for i, n in enumerate(reversed(r)):
        if round_:
            if r[-1] >= to_base / 2:
                m = 1
            round_ = False
            continue
        n += m
        m = 0
        if n >= to_base:
            m = 1
            n %= to_base
        ans += _number_to_letter(n)
    return ans[::-1]


def convert(
        from_base: int,
        to_base: int,
        n: NumType,
        accuracy: int = 6,
) -> Union[str, int, float]:
    if not isinstance(from_base, int):
        raise TypeError('`from_base` must be int')
    if not isinstance(to_base, int):
        raise TypeError('`to_base` must be int')
    if not isinstance(n, (str, int, float)):
        raise TypeError('`n` must be str, int or float')

    if not 2 <= to_base <= 36:
        raise ValueError('`from_base` must be in [2; 36]')
    if not 2 <= to_base <= 36:
        raise ValueError('`to_base` must be in [2; 36]')
    if isinstance(n, str) and not _check_str(n):
        raise ValueError('Invalid number')

    int_, frac, negative = _parse_num(n)
    if to_base == 10:
        return _make_num(_int_to_base10(from_base, int_),
                         _float_to_base10(from_base, frac, accuracy), negative)
    elif from_base == 10:
        return _make_num(_int_from_base10(to_base, int_),
                         _float_from_base10(to_base, frac, accuracy), negative)
    else:
        return _make_num(_int_from_base10(to_base, _int_to_base10(from_base, int_)),
                         _float_from_base10(to_base, _float_to_base10(from_base, frac, accuracy),
                                            accuracy), negative)


def main():
    from_base = int(input('Введите исходную СС: '))
    n = input('Введите число: ')
    to_base = int(input('Введите конечную СС: '))
    print(convert(from_base, to_base, n))


if __name__ == '__main__':
    main()
