#!/usr/bin/env python3

"""
This module renames all nodes with name so that name is unique. The "name" type
is also renamed so it uses last named value. Code is also checked for undefined
reference errors. Types with result also get name.
"""


def add_name(name, unique_name, scope):
    scope = {**scope, name: unique_name}
    return scope


def name_ast(ast, parent, scope):
    if ast['type'] == 'integer':
        return (ast, scope)
    if ast['type'] == 'name':
        return ({**ast, 'value': scope[ast['value']]}, scope)
    elif ast['type'] == 'def':
        name = ast['name']
        unique_name = f'{parent}.{name}'
        new_scope = add_name(name, unique_name, scope)

        expression, _ = name_ast(ast['expression'], unique_name, scope)
        return ({**ast, 'name': unique_name, 'expression': expression}, new_scope)
    elif ast['type'] == 'fn':
        inner_scope = scope
        for arg in ast['args']:
            inner_scope = add_name(arg, arg, inner_scope)

        expression, _ = name_ast(ast['expression'], '', inner_scope)
        return ({**ast, 'name': f'{parent}$fn', 'expression': expression}, scope)
    elif ast['type'] == 'external':
        return ({**ast, 'name': f'{parent}$external'}, scope)
    elif ast['type'] == 'call':
        call, _ = name_ast(ast['call'], f'{parent}$call', scope)

        args = []
        for i, arg in enumerate(ast['args']):
            arg, _ = name_ast(arg, f'{parent}$call{i}', scope)
            args.append(arg)

        return ({**ast, 'name': f'{parent}$res', 'call': call, 'args': args}, scope)
    elif ast['type'] == 'instruction':
        args = []
        for i, arg in enumerate(ast['args']):
            arg, _ = name_ast(arg, f'{parent}$call{i}', scope)
            args.append(arg)

        return ({**ast, 'name': f'{parent}$res', 'args': args}, scope)
    elif ast['type'] in ['block', 'tuple']:
        inner_scope = scope
        expressions = []
        for i, expression in enumerate(ast['expressions']):
            expression, inner_scope = name_ast(expression, f'{parent}${i}', inner_scope)
            expressions.append(expression)

        return ({**ast, 'expressions': expressions}, scope)


def namer(ast):
    ast, _ = name_ast(ast, '', dict())
    return ast


if __name__ == '__main__':
    import json
    import sys

    ast = json.load(sys.stdin)
    ast = namer(ast)
    json.dump(ast, sys.stdout, indent=2)
    sys.stdout.write('\n')
