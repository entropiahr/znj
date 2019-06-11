#!/usr/bin/env python3

"""
All "def" types are removed so that names which point to them change to point to
expression of that "def".
"""


def reference_expression(expression, scope):
    if expression['type'] == 'name':
        expression = scope.get(expression['value'], expression)
        scope[expression['value']] = expression
        return expression
    else:
        return expression


def reference_statements(old_statements, scope):
    statements = []
    for statement in old_statements:
        if statement['type'] == 'def':
            scope[statement['name']] = reference_expression(statement['expression'], scope)
        elif statement['type'] == 'fn':
            body, scope = reference_statements(statement['body'], scope)
            ret = reference_expression(statement['return'], scope)
            statements.append({**statement, 'body': body, 'return': ret})
        elif statement['type'] == 'external':
            statements.append(statement)
        elif statement['type'] == 'call':
            call = reference_expression(statement['call'], scope)
            args = [reference_expression(arg, scope) for arg in statement['args']]
            statements.append({**statement, 'call': call, 'args': args})
        elif statement['type'] == 'instruction':
            args = [reference_expression(arg, scope) for arg in statement['args']]
            statements.append({**statement, 'args': args})
        else:
            raise ValueError(f"Unimplemented statement: {statement['type']}")

    return (statements, scope)


def referencer(ast):
    statements, scope = reference_statements(ast['statements'], dict())
    expression = reference_expression(ast['expression'], scope)
    return {'expression': expression, 'statements': statements}


if __name__ == '__main__':
    import json
    import sys

    ast = json.load(sys.stdin)
    ast = referencer(ast)
    json.dump(ast, sys.stdout, indent=2)
    sys.stdout.write('\n')
