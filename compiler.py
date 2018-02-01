#!/usr/bin/env python3

from llvmlite import ir

int_type = ir.IntType(32)
env_cast_type = ir.PointerType(ir.IntType(8))

module = ir.Module()
module.triple = "x86_64-unknown-linux-gnu"

def type_to_ir(type):
    if type[0] == "Int":
        return ir.IntType(32)
    if type[0] == "->":
        arg_type = type_to_ir(type[1])
        ret_type = type_to_ir(type[2])
        function_type = ir.FunctionType(ret_type, [env_cast_type] + [arg_type])
        return ir.LiteralStructType((ir.PointerType(function_type), env_cast_type))
    raise ValueError("Unknown type: " + str(type))

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


def generate_def_fn(ast, builder, scope):
    name = ast["name"]
    fn = find_fn(name + ".fn")

    env_values = [generate_expression(e, builder, scope)[0] for e in ast["env"]]
    env_type = ir.LiteralStructType([e.type for e in env_values])
    env_ptr = builder.alloca(env_type, name=ast["name"] + ".env")
    for i, (value, e) in enumerate(zip(env_values, ast["env"])):
        indices = [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)]
        e_ptr = builder.gep(env_ptr, indices, name=ast["name"] + ".env." + e["name"])
        builder.store(value, e_ptr)
    env_ptr_cast = builder.bitcast(env_ptr, env_cast_type, ast["name"] + ".envcast")

    fn_struct = ir.Constant.literal_struct((fn, ir.Constant(env_ptr_cast.type, None)))
    fn_struct = builder.insert_value(fn_struct, env_ptr_cast, 1, name)

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
    call, *args = [generate_expression(arg, builder, scope)[0] for arg in ast["args"]]
    def single_call(call, args):
        if not args: return call
        fn = builder.extract_value(call, 0)
        env = builder.extract_value(call, 1)

        arg, *args = args
        call = builder.call(fn, [env, arg])
        return single_call(call, args)

    value = single_call(call, args)
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

    env_ptr, *arg_values = fn.args
    env_type = ir.LiteralStructType([type_to_ir(e["vtype"]) for e in ast["env"]])
    env_ptr = builder.bitcast(env_ptr, ir.PointerType(env_type), ".env")
    def get_env_value(i, e):
        indices = [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)]
        ptr = builder.gep(env_ptr, indices, name=".env." + e["name"])
        return builder.load(ptr, name=e["name"])
    env_values = [get_env_value(i, e) for i, e in enumerate(ast["env"])]
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

    arg_names = [".envcast"] + arg_names
    arg_types = [env_cast_type] + arg_types

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
