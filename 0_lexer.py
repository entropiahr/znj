#!/usr/bin/env python3

def scan_integer(c, chars):
    integer = c

    while chars:
        c, *next_chars = chars
        if not c.isnumeric():
            break
        chars = next_chars
        integer += c

    return (integer, chars)

def scan_name(c, chars):
    name = c

    while chars:
        c, *next_chars = chars
        if not (c.isalnum() or c == '_'):
            break
        chars = next_chars
        name += c

    return (name, chars)


def lexer(chars):
    while chars:
        c, *chars = chars
        if c in '\n\t ':
            pass
        elif c == '=':
            yield {'type': 'def'}
        elif c == ';':
            yield {'type': 'term'}
        elif c.isnumeric():
            integer, chars = scan_integer(c, chars)
            yield {'type': 'integer', 'value': integer}
        elif c.isalpha() or c == '_':
            name, chars = scan_name(c, chars)
            if name == 'instruction':
                yield {'type': 'instruction'}
            elif name == 'external':
                yield {'type': 'external'}
            else:
                yield {'type': 'name', 'name': name}
        else:
            raise ValueError(f"Unrecognised character: {repr(c)}.")


if __name__ == '__main__':
    import json
    import sys

    lexed_list = list(lexer(sys.stdin.read()))
    json.dump(lexed_list, sys.stdout)
    sys.stdout.write('\n')
