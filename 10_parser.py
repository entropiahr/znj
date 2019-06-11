#!/usr/bin/env python3

"""
This module is first task of a parser.
It creates AST by following rules described below.

Rules:
literal
name
name|literal|def|def_fn|call|block|instruction -> expression, referenced as "ex"
name = ex -> definition, referenced as "def"
name (name, name...) -> ex - definition, referenced as "def_fn"
instruction name (ex, ex...) -> instruction
external name (name, name...) -> instruction
ex (ex, ex...) -> function call, referenced as "call"
(ex; ex...) -> parsed as a block, referenced as "block"

AST node types:
{"type": "integer", "value": number}
{"type": "name", "value": string}
{"type": "instruction", "instruction": string, "args", [AST]}
{"type": "external", "name": string, "args": [string]}
{"type": "def", "name": string, "expression": AST}
{"type": "fn", "args": [string], "expression": AST}
{"type": "call", "call": AST, "args": [AST]}
{"type": "block", "expressions": [AST]}
"""


def parse_call(call, args):
    if args['type'] == 'tuple':
        return {'type': 'call', 'call': call, 'args': args['expressions']}
    else:
        raise ValueError(f"Unexpected expression for function arguments {args}.")


def parse_fn(args, expression):
    if args['type'] == 'tuple':
        arg_names = []
        for arg in args['expressions']:
            if arg['type'] == 'name':
                arg_names.append(arg['value'])
            else:
                raise ValueError("Unexpected expression for argument definition.")
        return {'type': 'fn', 'args': arg_names, 'expression': expression}
    else:
        raise ValueError(f"Unexpected expression for function arguments {args}.")


def parse_def(definition, expression):
    if definition['type'] == 'name':
        return {'type': 'def', 'name': definition['value'], 'expression': expression}
    else:
        raise ValueError(f"Unexpected expression for value definition {definition}.")


def parse_operator(operator):
    lhs = parse_expression(operator['lhs'])
    rhs = parse_expression(operator['rhs'])
    if operator['operator'] == '=':
        return parse_def(lhs, rhs)
    if operator['operator'] == '->':
        return parse_fn(lhs, rhs)
    if operator['operator'] == 'call':
        return parse_call(lhs, rhs)
    else:
        raise ValueError(f"Unsupported operator: {operator['operator']}")


def parse_instruction(instruction):
    args = [parse_expression(arg) for arg in instruction['args']]
    return {**instruction, 'args': args}


def parse_expression(ast):
    if ast['type'] in ['integer', 'name', 'external']:
        return ast
    elif ast['type'] == 'instruction':
        return parse_instruction(ast)
    elif ast['type'] == 'block':
        return parse_block(ast)
    elif ast['type'] == 'operator':
        return parse_operator(ast)


def parse_block(ast):
    expressions = [parse_expression(ex) for ex in ast['expressions']]
    if ast['seperator'] == ';':
        return {'type': 'block', 'expressions': expressions}
    else:
        return {'type': 'tuple', 'expressions': expressions}


def parser(ast):
    return parse_block(ast)


if __name__ == '__main__':
    import json
    import sys

    ast = json.load(sys.stdin)
    ast = parser(ast)
    json.dump(ast, sys.stdout, indent=2)
    sys.stdout.write('\n')
