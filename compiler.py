#!/usr/bin/env python3

from llvmlite import ir

int_type = ir.IntType(32)

module = ir.Module()
module.triple = "x86_64-unknown-linux-gnu"


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

    def add_fn(self, name, fn):
        new = self.__class__(self)
        new.values = self.values.copy()
        new.values[name] = lambda builder, args: builder.call(fn, args)
        return new

    def add_fn_env(self, name, fn_struct):
        new = self.__class__(self)
        new.values = self.values.copy()

        def call(builder, args):
            fn = builder.extract_value(fn_struct, 0, name)
            env = builder.extract_value(fn_struct, 1, name)
            builder.call(fn, [env] + args)

        new.values[name] = lambda builder, args: builder.call(fn, [env] + args)
        return new

    def call(self, name):
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
    scope = scope.add_fn(name, fn)
    return (fn, scope)

def generate_def_name(ast, builder, scope):
    name = ast["name"]
    value, _ = generate_expression(ast["body"], builder, scope)
    scope = scope.add_value(name, value)
    return (value, scope)

def generate_integer(ast, builder, scope):
    return (ir.Constant(int_type, ast["value"]), scope)

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
    env_names = ast["env"]
    if ast["env"]:
        env_struct, *args = fn.args
        env_values = [builder.extract_value(env_struct, i, name) for i, name in enumerate(env_names)]
        scope_values = [(x.name, x) for x in env_values + args]
    else:
        scope_values = [(arg.name, arg) for arg in fn.args]

    for name, value in scope_values:
        scope = scope.add_value(name, value)

    value, _ = generate_expression(ast["body"], builder, scope)

    builder.ret(value)

def declare_fn(ast):
    name = ast["name"]

    env_names = ast["env"]
    if env_names:
        env_type = ir.LiteralStructType([int_type for x in env_names])
    else:
        env_type = None

    arg_names = ast["args"]
    arg_types = tuple(int_type for x in arg_names)
    if env_names:
        arg_names = [".env"] + arg_names
        arg_types = (env_type,) + arg_types

    fn = ir.Function(module, ir.FunctionType(int_type, arg_types), name=name)
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

    declare_fn(ast["main"])
    generate_fn(ast["main"], scope)

    return str(module)


if __name__ == "__main__":
    import json
    import sys

    ast = json.load(sys.stdin)
    llvm_ir = generate_ast(ast)
    sys.stdout.write(llvm_ir)
