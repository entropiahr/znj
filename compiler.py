#!/usr/bin/env python3

from llvmlite import ir

int_type = ir.IntType(32)

module = ir.Module()
module.triple = "x86_64-unknown-linux-gnu"

def type_to_ir(type):
    if type[0] == "Int":
        return ir.IntType(32)
    raise ValueError("Unknown type: " + str(type))
    if type[0] == "a":
        return ir.IntType(32)
    elif type[0] == "->":
        arg_types = []
        while type[0] == "->":
            arg_types.append(type_to_ir(type[1]))
            type = type[2]
        ret_type = type_to_ir(type)
        return ir.FunctionType(ret_type, arg_types)

class Scope:
    def __init__(self):
        self.values = dict()

    def add(self, name, value):
        new = self.__class__()
        new.values = self.values.copy()
        new.values[name] = value
        return new

    def find(self, name):
        return self.values[name]


def build_struct(builder, values, name=""):
    struct_type = ir.LiteralStructType([v.type for v in values])
    struct = ir.Constant(struct_type, ir.Undefined)
    for i, e in enumerate(values):
        is_last = i == len(values) -1
        if name and not is_last:
            step_name = name + "." + str(i)
        else:
            step_name = name
        struct = builder.insert_value(struct, e, i, step_name)
    return struct

def generate_def_fn(ast, builder, scope):
    name = ast["name"]
    fn = find_fn(name + ".fn")

    env_values = [generate_expression(e, builder, scope)[0] for e in ast["env"]]
    env_struct = build_struct(builder, env_values, ast["name"] + ".env")

    fn_struct = build_struct(builder, (fn, env_struct), ast["name"])

    scope = scope.add(name, fn_struct)

    return (fn_struct, scope)

def generate_def_name(ast, builder, scope):
    name = ast["name"]
    value, _ = generate_expression(ast["body"], builder, scope)
    scope = scope.add(name, value)
    return (value, scope)

def generate_name(ast, builder, scope):
    value = scope.find(ast["name"])
    return (value, scope)

def generate_call(ast, builder, scope):
    fn_struct, *args = [generate_expression(arg, builder, scope)[0] for arg in ast["args"]]

    fn = builder.extract_value(fn_struct, 0)
    env = builder.extract_value(fn_struct, 1)

    value = builder.call(fn, [env] + args)

    return (value, scope)

def generate_block(ast, builder, scope):
    child_scope = scope
    for e in ast["body"]:
        value, child_scope = generate_expression(e, builder, child_scope)
    return (value, scope)

def generate_integer(ast, builder, scope):
    return (ir.Constant(type_to_ir(ast["vtype"]), ast["value"]), scope)

def generate_instruction(ast, builder, scope):
    if ast["name"] == "add":
        lhs, rhs = [generate_expression(arg, builder, scope)[0] for arg in ast["args"]]
        value = builder.add(lhs, rhs)
        return (value, scope)
    else:
        raise ValueError("Unknown instruction: " + ast["name"])

def generate_expression(ast, builder, scope):
    if ast["type"] == "def_name":
        return generate_def_name(ast, builder, scope)
    elif ast["type"] == "def_fn":
        return generate_def_fn(ast, builder, scope)
    elif ast["type"] == "name":
        return generate_name(ast, builder, scope)
    elif ast["type"] == "call":
        return generate_call(ast, builder, scope)
    elif ast["type"] == "block":
        return generate_block(ast, builder, scope)
    elif ast["type"] == "integer":
        return generate_integer(ast, builder, scope)
    elif ast["type"] == "instruction":
        return generate_instruction(ast, builder, scope)
    else:
        raise ValueError("Wrong type: " + str(ast["type"]))

def generate_fn(ast):
    fn = find_fn(ast["name"] + ".fn")

    block = fn.append_basic_block("entry")
    builder = ir.IRBuilder(block)

    env_struct, *arg_values = fn.args
    env_values = [builder.extract_value(env_struct, i, e["name"]) for i, e in enumerate(ast["env"])]
    scope_values = [(x.name, x) for x in env_values + arg_values]

    scope = Scope()
    for name, value in scope_values:
        scope = scope.add(name, value)

    value, _ = generate_expression(ast["body"], builder, scope)

    builder.ret(value)

def declare_fn(ast):
    args = ast["args"]

    ret_type = type_to_ir(ast["ret_type"])

    arg_names = [arg["name"] for arg in args]
    arg_types = [type_to_ir(arg["vtype"]) for arg in args]

    env_type = ir.LiteralStructType([type_to_ir(e["vtype"]) for e in ast["env"]])
    arg_names = [".env"] + arg_names
    arg_types = [env_type] + arg_types

    fn = ir.Function(module, ir.FunctionType(ret_type, arg_types), name=ast["name"] + ".fn")
    fn.args = tuple(ir.Argument(fn, t, n) for t, n in zip(arg_types, arg_names))

def generate_main(main_body):
    fn = ir.Function(module, ir.FunctionType(ir.IntType(32), ()), name="main")

    block = fn.append_basic_block("entry")
    builder = ir.IRBuilder(block)

    value, _ = generate_expression(main_body, builder, Scope())
    builder.ret(value)

def find_fn(name):
    fn, *tail = [x for x in module.functions if x.name == name]
    return fn

def generate_ast(ast):
    for fn in ast["fns"]:
        declare_fn(fn)
    for fn in ast["fns"]:
        generate_fn(fn)

    generate_main(ast["main"])

    return str(module)


if __name__ == "__main__":
    import json
    import sys

    ast = json.load(sys.stdin)
    llvm_ir = generate_ast(ast)
    sys.stdout.write(llvm_ir)
