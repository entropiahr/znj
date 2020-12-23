#!/usr/bin/env python3

"""
This module creates list of tokens.

Single character tokens allways seperate, other tokens seperate by space or
other single character tokens.

Space is new line, tab or space and is not converted to tokens.

Tokens types:
{"type": syntax}
{"type": "integer", "value": number}
{"type": "name", "value": string}
{"type": "EOF"}
"""

import re

SYNTAX = ['=>', '->', ':', '=', ';', ',', '(', ')', 'instruction', 'external']


def scan(regex, chars):
    m = re.match(regex, chars)

    if m:
        return (m.group(0), chars[m.end():])
    else:
        return (None, chars)


def lex(chars):
    if not chars:
        return []

    empty, chars = scan(r'\s', chars)
    if empty:
        return lex(chars)

    for syntax in SYNTAX:
        if chars.startswith(syntax):
            return [{'type': syntax}] + lex(chars[len(syntax):])

    number, chars = scan(r'-?\d+', chars)
    if number:
        return [{'type': 'integer', 'value': number}] + lex(chars)

    name, chars = scan(r'[^\W\d]\w*', chars)
    if name:
        return [{'type': 'name', 'value': name}] + lex(chars)

    raise ValueError(f"Unrecognised character: {repr(chars[0])}.")


def lexer(chars):
    return lex(chars) + [{'type': 'EOF'}]


if __name__ == '__main__':
    import json
    import sys

    ast = list(lexer(sys.stdin.read()))
    json.dump(ast, sys.stdout, indent=2)
    sys.stdout.write('\n')
