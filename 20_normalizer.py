#!/usr/bin/env python3

"""
This module normalizes AST. All functions are transfered to global scope.
This is a last possible step that will modify AST as much as possible before
converting it to llvmir.

function:
{"name": string, "external": false, "args": [string], "body": [statement], "return": expression}
{"name": string, "external": true}

literal:
{"type": "integer", "value": number}

name:
{"type": "name", "value": string}

name|literal -> expression

statement:
{"type": "call", "name": string, "call": expression, "args": [expression]}
{"type": "instruction", "instruction": string, "name": string, "args", [expression]}

AST:
{"functions": [function]}
"""


def normalize_statement(statement):
    if statement['type'] == 'call':
        return statement
    elif statement['type'] == 'instruction':
        return statement
    else:
        raise ValueError(f"Unimplemented statement in function body: {statement['type']}")


def normalize_fn(fn):
    body = [normalize_statement(statement) for statement in fn['body']]

    return {
        'name': fn['name'],
        'external': False,
        'args': fn['args'],
        'body': body,
        'return': fn['return'],
    }


def normalizer(ast):
    functions = []

    for statement in ast['statements']:
        if statement['type'] == 'fn':
            functions.append(normalize_fn(statement))
        elif statement['type'] == 'external':
            functions.append({'name': statement['name'], 'external': True})
        else:
            raise ValueError("Global scope can only have function definitions.")

    return {"functions": functions}


if __name__ == '__main__':
    import json
    import sys

    ast = json.load(sys.stdin)
    ast = normalizer(ast)
    json.dump(ast, sys.stdout, indent=2)
    sys.stdout.write('\n')
