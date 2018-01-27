#!/usr/bin/env python3

from llvmlite import ir

int_type = ir.IntType(32)

module = ir.Module()
module.triple = "x86_64-unknown-linux-gnu"

def type_to_ir(type):
    if type[0] == "Int":
        return ir.IntType(32)
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
    def __init__(self, parent):
        if parent:
            self.values = parent.values.copy()

    @classmethod
    def root(cls, internal_calls):
        scope = cls(None)
        scope.values = internal_calls
        return scope

    def add_value(self, name, value):
        new = self.__class__(self)
        new.values = self.values.copy()
        new.values[name] = lambda builder, args: value
        return new

    def add_fn_env(self, name, fn_struct):
        new = self.__class__(self)
        new.values = self.values.copy()

        def call(builder, args):
            fn = builder.extract_value(fn_struct, 0, name)
            env = builder.extract_value(fn_struct, 1, name)
            builder.call(fn, [env] + args)

        new.values[name] = call
        return new

    def call(self, name):
        call = self.values.get(name)
        if call: return call
        return lambda builder, args: builder.call(find_fn(name), args)


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

def generate_def_fn_env(ast, builder, scope):
    name = ast["name"]
    fn = find_fn(name)

    env_values = [generate_expression(e, builder, scope)[0] for e in ast["env"]]
    env_struct = build_struct(builder, env_values, ast["name"] + ".env")

    fn_struct = build_struct(builder, (fn, env_struct), ast["name"] + ".fn")

    scope = scope.add_fn_env(name, fn_struct)

    return (fn_struct, scope)

def generate_def_fn_simple(ast, builder, scope):
    name = ast["name"]
    fn = find_fn(name)
    return (fn, scope)

def generate_def_name(ast, builder, scope):
    name = ast["name"]
    value, _ = generate_expression(ast["body"], builder, scope)
    scope = scope.add_value(name, value)
    return (value, scope)

def generate_integer(ast, builder, scope):
    return (ir.Constant(type_to_ir(ast["vtype"]), ast["value"]), scope)

def generate_call(ast, builder, scope):
    args = [generate_expression(arg, builder, scope)[0] for arg in ast["args"]]
    call = scope.call(ast["name"])

    return (call(builder, args), scope)

def generate_block(ast, builder, scope):
    child_scope = Scope(scope)
    for e in ast["body"]:
        value, child_scope = generate_expression(e, builder, child_scope)
    return (value, scope)

def generate_expression(ast, builder, scope):
    if ast["type"] == "def_fn_env":
        return generate_def_fn_env(ast, builder, scope)
    elif ast["type"] == "def_fn_simple":
        return generate_def_fn_simple(ast, builder, scope)
    elif ast["type"] == "def_name":
        return generate_def_name(ast, builder, scope)
    elif ast["type"] == "integer":
        return generate_integer(ast, builder, scope)
    elif ast["type"] == "call":
        return generate_call(ast, builder, scope)
    elif ast["type"] == "block":
        return generate_block(ast, builder, scope)
    else:
        raise ValueError("Wrong type: " + str(ast["type"]))

def generate_fn(ast, root_scope):
    fn = find_fn(ast["name"])

    block = fn.append_basic_block("entry")
    builder = ir.IRBuilder(block)

    scope = Scope(root_scope)
    env = ast.get("env")
    if env:
        env_struct, *arg_values = fn.args
        env_values = [builder.extract_value(env_struct, i, e["name"]) for i, e in enumerate(env)]
        scope_values = [(x.name, x) for x in env_values + arg_values]
    else:
        scope_values = [(x.name, x) for x in fn.args]

    for name, value in scope_values:
        scope = scope.add_value(name, value)

    value, _ = generate_expression(ast["body"], builder, scope)

    builder.ret(value)

def declare_fn(ast, *, is_main=False):
    name = ast["name"]
    args = ast["args"]

    type = ast["vtype"]
    for arg in args:
        assert type[0] == "->"
        type = type[2]
    ret_type = type_to_ir(type)

    arg_names = [arg["name"] for arg in args]
    arg_types = [type_to_ir(arg["vtype"]) for arg in args]

    env = ast.get("env")
    if env:
        env_type = ir.LiteralStructType([type_to_ir(e["vtype"]) for e in env])
        arg_names = [".env"] + arg_names
        arg_types = [env_type] + arg_types

    fn = ir.Function(module, ir.FunctionType(ret_type, arg_types), name=name)
    fn.args = tuple(ir.Argument(fn, t, n) for t, n in zip(arg_types, arg_names))

def find_fn(name):
    fn, *tail = [x for x in module.functions if x.name == name]
    return fn

def generate_ast(ast):
    fns = ast["fns"]
    for fn in fns:
        declare_fn(fn)

    scope = Scope.root({
        "add": lambda builder, args: builder.add(args[0], args[1])
    })
    for fn in fns:
        generate_fn(fn, scope)

    main_ast = {
        "name": "main",
        "args": [],
        "vtype": ["Int"],
        "body": ast["main"]
    }
    declare_fn(main_ast, is_main=True)
    generate_fn(main_ast, scope)

    return str(module)


if __name__ == "__main__":
    import json
    import sys

    ast = json.load(sys.stdin)
    llvm_ir = generate_ast(ast)
    sys.stdout.write(llvm_ir)
