#!/usr/bin/env python3

"""
This creates LLVM IR code from generated AST.
"""

from llvmlite import ir

int_type = ir.IntType(32)
env_cast_type = ir.PointerType(ir.IntType(8))

module = ir.Module()
module.triple = r"x86_64-unknown-linux-gnu"


def get_expression(expression, scope):
    if expression['type'] == 'name':
        return scope[expression['value']]
    elif expression['type'] == 'integer':
        return ir.Constant(ir.IntType(32), expression['value'])
    else:
        raise ValueError(f"Unimplemented expression: {expression['type']}")


def generate_instruction(builder, statement, scope):
    args = [get_expression(arg, scope) for arg in statement['args']]

    if statement['instruction'] == 'add':
        if len(args) == 2:
            value = builder.add(args[0], args[1], name=statement['name'])
        else:
            raise ValueError(f"Wrong number of instruction arguments.")
    elif statement['instruction'] == 'sub':
        if len(args) == 2:
            value = builder.sub(args[0], args[1], name=statement['name'])
        else:
            raise ValueError(f"Wrong number of instruction arguments.")
    else:
        raise ValueError(f"Unimplemented instruction: {statement['instruction']}")

    scope[statement['name']] = value

    return scope


def generate_call(builder, statement, scope):
    call = get_expression(statement['call'], scope)
    args = [get_expression(arg, scope) for arg in statement['args']]

    value = builder.call(call, args, name=statement['name'])

    scope[statement['name']] = value

    return scope


def generate_statement(builder, statement, scope):
    if statement['type'] == 'call':
        return generate_call(builder, statement, scope)
    if statement['type'] == 'instruction':
        return generate_instruction(builder, statement, scope)
    else:
        raise ValueError(f"Unimplemented statement: {statement['type']}")


def generate_fn_body(fn, scope):
    function = scope[fn['name']]
    block = function.append_basic_block('entry')
    builder = ir.IRBuilder(block)

    for arg in function.args:
        scope[arg.name] = arg

    for statement in fn['body']:
        scope = generate_statement(builder, statement, scope)

    ret = get_expression(fn['return'], scope)
    builder.ret(ret)


def declare_fn(fn):
    if fn['external']:
        type = ir.FunctionType(int_type, (int_type,))
    else:
        type = ir.FunctionType(int_type, (int_type,)*len(fn['args']))
    function = ir.Function(module, type, name=fn['name'])

    if not fn['external']:
        for arg, arg_name in zip(function.args, fn['args']):
            arg.name = arg_name

    return function


def compiler(ast):
    scope = dict()

    for fn in ast['functions']:
        scope[fn['name']] = declare_fn(fn)
    for fn in ast['functions']:
        if not fn['external']:
            generate_fn_body(fn, scope)

    return str(module)


if __name__ == '__main__':
    import json
    import sys

    ast = json.load(sys.stdin)
    llvm_ir = compiler(ast)
    sys.stdout.write(llvm_ir)
