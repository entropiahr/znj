#!/usr/bin/env python3

"""
This module is first task of a parser.
It creates AST by following rules described below.

Rules:
literal
name
name = ex -> definition
(name, name...) => ex - function
instruction name (ex, ex...) -> instruction
external name -> external
ex (ex, ex...) -> function call
(ex; ex...) -> block

AST node types:
{"type": "integer", "value": number}
{"type": "name", "value": string}
{"type": "instruction", "instruction": string, "args", [AST]}
{"type": "external", "name": string}
{"type": "def", "name": string, "expression": AST}
{"type": "fn", "args": [string], "expression": AST}
{"type": "call", "call": AST, "args": [AST]}
{"type": "block", "expressions": [AST]}
"""


def parse_call(call, args):
    if args['type'] == 'tuple':
        return {'type': 'call', 'call': call, 'args': args['expressions']}
    else:
        raise ValueError(f"Unexpected expression for function arguments: {args}")


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
        raise ValueError(f"Unexpected expression for function arguments: {args}")


def parse_type(type):
    if type['type'] == 'name':
        if type['value'] == 'Int':
            return {'type': 'type', 'ttype': 'primitive', 'value': 'Int'}
        else:
            raise ValueError(f"Unsupported type: {type}")
    elif type['type'] == 'type':
        return type
    else:
        raise ValueError(f"Unexpected expression for type {type}.")


def parse_type_fn(lhs, rhs):
    if lhs['type'] == 'tuple':
        args = []
        for arg in lhs['expressions']:
            args.append(parse_type(arg))

        result = parse_type(rhs)
        return {'type': 'type', 'ttype': 'function', 'args': args, 'result': result}
    else:
        raise ValueError(f"Unexpected expression for function type {lhs}.")


def parse_type_signature(type, target):
    type = parse_type(type)
    return {**target, 'vtype': type}


def parse_def(definition, expression):
    if definition['type'] == 'name' and 'vtype' in definition:
        vtype = definition['vtype']
        name = definition['value']
        return {'type': 'def', 'vtype': vtype, 'name': name, 'expression': expression}
    else:
        raise ValueError(f"Unexpected expression for value definition: {definition}")


def parse_operator(operator):
    lhs = parse_expression(operator['lhs'])
    rhs = parse_expression(operator['rhs'])
    if operator['operator'] == 'call':
        return parse_call(lhs, rhs)
    elif operator['operator'] == '=>':
        return parse_fn(lhs, rhs)
    elif operator['operator'] == '->':
        return parse_type_fn(lhs, rhs)
    elif operator['operator'] == ':':
        return parse_type_signature(lhs, rhs)
    elif operator['operator'] == '=':
        return parse_def(lhs, rhs)
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
