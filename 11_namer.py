#!/usr/bin/env python3

"""
This module renames all nodes with name so that name is unique. The "name" type
is also renamed so it uses last named value. Code is also checked for undefined
reference errors. Types with result also get name.
"""


def get_unique_name(name, scope):
    id = scope[name]
    if id == 'empty':
        return name
    else:
        unique_name = f'{name}.{scope[name]}'
        return unique_name


def add_name(name, scope):
    id = scope.get(name, None)
    if id is None:
        scope = {**scope, name: 'empty'}
        return (name, scope)
    else:
        if id == 'empty':
            id = 0
        else:
            id = id + 1

        unique_name = f'{name}.{id}'
        scope = {**scope, name: id}

        return (unique_name, scope)


def name_ast(ast, requested_name, parent, scope):
    if requested_name:
        name = requested_name
    else:
        name = parent

    if ast['type'] == 'integer':
        return (ast, scope)
    if ast['type'] == 'name':
        unique_name = get_unique_name(ast['value'], scope)
        return ({**ast, 'value': unique_name}, scope)
    elif ast['type'] == 'def':
        name = ast['name']
        name, new_scope = add_name(name, scope)

        if requested_name:
            name = requested_name

        expression, _ = name_ast(ast['expression'], name, parent, scope)

        return ({**ast, 'name': name, 'expression': expression}, new_scope)
    elif ast['type'] == 'fn':
        inner_scope = scope
        args = []
        for arg in ast['args']:
            arg, inner_scope = add_name(arg, inner_scope)
            args.append(arg)

        expression, _ = name_ast(ast['expression'], None, '.ret', inner_scope)
        return ({**ast, 'name': name, 'expression': expression}, scope)
    elif ast['type'] == 'external':
        return ({**ast, 'name': name}, scope)
    elif ast['type'] == 'call':
        call, _ = name_ast(ast['call'], None, f'{parent}.call', scope)

        args = []
        for i, arg in enumerate(ast['args']):
            arg, _ = name_ast(arg, None, f'{parent}.call{i}', scope)
            args.append(arg)

        return ({**ast, 'name': name, 'call': call, 'args': args}, scope)
    elif ast['type'] == 'instruction':
        args = []
        for i, arg in enumerate(ast['args']):
            arg, _ = name_ast(arg, None, f'{parent}.instruction{i}', scope)
            args.append(arg)

        return ({**ast, 'name': name, 'args': args}, scope)
    elif ast['type'] in ['block', 'tuple']:
        inner_scope = scope
        expressions = []
        for i, expression in enumerate(ast['expressions']):
            if i == len(ast['expressions']) - 1:
                expression_name = name
            else:
                expression_name = None

            expression, inner_scope = name_ast(expression, None, f'{parent}.{i}', inner_scope)
            expressions.append(expression)

        return ({**ast, 'expressions': expressions}, scope)


def namer(ast):
    ast, _ = name_ast(ast, None, '.module', dict())
    return ast


if __name__ == '__main__':
    import json
    import sys

    ast = json.load(sys.stdin)
    ast = namer(ast)
    json.dump(ast, sys.stdout, indent=2)
    sys.stdout.write('\n')
