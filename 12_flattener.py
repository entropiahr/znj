#!/usr/bin/env python3

"""
This module flattens the AST.

AST is flattened by removing "block" type and giving all "fn" types a body which
is a list of statements.

Statement is any kind of program operation, while expression is a reference to a
value which can be a name or a literal.

literal:
{"type": "integer", "value": number}

name:
{"type": "name", "value": string}

name|literal -> expression

statement:
{"type": "def", "name": string, "expression": expression}
{"type": "fn", "args": [string], "name": string, "body": [statement], "return": expression}
{"type": "external", "external": string, "name": string}
{"type": "call", "name": string, "call": expression, "args": [expression]}
{"type": "instruction", "instruction": string, "name": string, "args", [expression]}

AST:
{"statements": [statement], "expression", expression}
"""


def flatten_ast(ast):
    if ast['type'] in ['integer', 'name']:
        return (ast, [])
    elif ast['type'] == 'def':
        expression, statements = flatten_ast(ast['expression'])
        return ({
            'type': 'name',
            'value': ast['name'],
        }, statements + [{**ast, 'expression': expression}])
    elif ast['type'] == 'fn':
        ret, body = flatten_ast(ast['expression'])
        return ({
            'type': 'name',
            'value': ast['name'],
        }, [{
            'type': 'fn',
            'args': ast['args'],
            'name': ast['name'],
            'body': body,
            'return': ret,
        }])
    elif ast['type'] == 'external':
        return ({
            'type': 'name',
            'value': ast['name'],
        }, [ast])
    elif ast['type'] == 'call':
        statements = []

        args = []
        for arg in ast['args']:
            arg_expression, arg_statements = flatten_ast(arg)
            args.append(arg_expression)
            statements += arg_statements

        call_expression, call_statements = flatten_ast(ast['call'])
        call = call_expression
        statements += call_statements

        return ({
            'type': 'name',
            'value': ast['name'],
        }, statements + [{
            'type': 'call',
            'name': ast['name'],
            'call': call,
            'args': args,
        }])
    elif ast['type'] == 'instruction':
        statements = []

        args = []
        for arg in ast['args']:
            arg_expression, arg_statements = flatten_ast(arg)
            args.append(arg_expression)
            statements += arg_statements

        return ({
            'type': 'name',
            'value': ast['name'],
        }, statements + [{
            'type': 'instruction',
            'instruction': ast['instruction'],
            'name': ast['name'],
            'args': args,
        }])
    elif ast['type'] == 'block':
        statements = []
        for child in ast['expressions']:
            child_expression, child_statements = flatten_ast(child)
            expression = child_expression
            statements += child_statements

        return (expression, statements)
    else:
        raise ValueError(f"Unimplemented AST: {ast}")


def flattener(ast):
    expression, statements = flatten_ast(ast)
    return {'expression': expression, 'statements': statements}


if __name__ == '__main__':
    import json
    import sys

    ast = json.load(sys.stdin)
    ast = flattener(ast)
    json.dump(ast, sys.stdout, indent=2)
    sys.stdout.write('\n')
