#!/usr/bin/env python3

from llvmlite import ir

int_type = ir.IntType(32)
env_cast_type = ir.PointerType(ir.IntType(8))

module = ir.Module()
module.triple = r"x86_64-unknown-linux-gnu"

def type_to_ir(type):
    if type[0] == 'Int':
        return ir.IntType(32)
    if type[0] == '->':
        arg_type = type_to_ir(type[1])
        ret_type = type_to_ir(type[2])
        function_type = ir.FunctionType(ret_type, [env_cast_type] + [arg_type])
        return ir.LiteralStructType((ir.PointerType(function_type), env_cast_type))
    raise ValueError(f"Unknown type: {type}")

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


def generate_def(ast, builder, scope):
    name = ast['name']
    value, _ = generate_expression(ast['body'], builder, scope)
    scope = scope.add(name, value)
    return (value, scope)

def generate_fn(ast, builder, scope):
    name = ast['name']
    fn = find_fn(name + '.fn')

    env_values = [generate_expression(e, builder, scope)[0] for e in ast['env']]
    env_type = ir.LiteralStructType([e.type for e in env_values])
    env_ptr = builder.alloca(env_type, name=name + '.env')
    for i, (value, e) in enumerate(zip(env_values, ast['env'])):
        indices = [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)]
        e_ptr = builder.gep(env_ptr, indices, name=name + '.env.' + e['name'])
        builder.store(value, e_ptr)
    env_ptr_cast = builder.bitcast(env_ptr, env_cast_type, name + '.envcast')

    fn_struct = ir.Constant.literal_struct((fn, ir.Constant(env_cast_type, None)))
    fn_struct = builder.insert_value(fn_struct, env_ptr_cast, 1, name)

    scope = scope.add(name, fn_struct)

    return (fn_struct, scope)

def generate_name(ast, builder, scope):
    value = scope.find(ast['name'])
    return (value, scope)

def generate_call(ast, builder, scope):
    call, _ = generate_expression(ast['call'], builder, scope)
    arg, _ = generate_expression(ast['arg'], builder, scope)

    fn = builder.extract_value(call, 0, name=ast['name'] + '.fn')
    env = builder.extract_value(call, 1, name=ast['name'] + '.env')

    value = builder.call(fn, [env, arg], name=ast['name'])

    return (value, scope)

def generate_block(ast, builder, scope):
    child_scope = scope
    for e in ast['body']:
        value, child_scope = generate_expression(e, builder, child_scope)
    return (value, scope)

def generate_integer(ast, builder, scope):
    return (ir.Constant(type_to_ir(ast['vtype']), ast['value']), scope)

def generate_instruction(ast, builder, scope):
    if ast['instruction'] == 'add':
        lhs, rhs = [generate_expression(arg, builder, scope)[0] for arg in ast['args']]
        value = builder.add(lhs, rhs, name=ast['name'])
        return (value, scope)
    else:
        raise ValueError(f"Unknown instruction: {ast['name']}")

def generate_external(ast, builder, scope):
    arg_values = []
    for arg in ast['args']:
        arg_value, _ = generate_expression(arg, builder, scope)
        arg_values.append(arg_value)

    fn = find_fn(ast['name'])
    value = builder.call(fn, arg_values, name='.ret')

    return (value, scope)


def generate_expression(ast, builder, scope):
    if ast['type'] == 'def':
        return generate_def(ast, builder, scope)
    elif ast['type'] == 'fn':
        return generate_fn(ast, builder, scope)
    elif ast['type'] == 'name':
        return generate_name(ast, builder, scope)
    elif ast['type'] == 'call':
        return generate_call(ast, builder, scope)
    elif ast['type'] == 'block':
        return generate_block(ast, builder, scope)
    elif ast['type'] == 'integer':
        return generate_integer(ast, builder, scope)
    elif ast['type'] == 'instruction':
        return generate_instruction(ast, builder, scope)
    elif ast['type'] == 'external':
        return generate_external(ast, builder, scope)
    else:
        raise ValueError(f"Wrong type: {ast['type']}")

def declare_external(ast):
    ret_type = type_to_ir(['Int'])
    arg_types = [type_to_ir(arg['vtype']) for arg in ast['args']]
    arg_names = [arg['name'] for arg in ast['args']]

    fn = ir.Function(module, ir.FunctionType(ret_type, arg_types), name=ast['name'])
    fn.args = tuple(ir.Argument(fn, t, n) for t, n in zip(arg_types, arg_names))

def declare_fn(ast):
    ret_type = type_to_ir(ast['ret_type'])

    arg = ast['arg']
    arg_names = ('.envcast', arg['name'])
    arg_types = (env_cast_type, type_to_ir(arg['vtype']))

    fn = ir.Function(module, ir.FunctionType(ret_type, arg_types), name=ast['name'])
    fn.args = tuple(ir.Argument(fn, t, n) for t, n in zip(arg_types, arg_names))

def generate_fn_body(ast):
    fn = find_fn(ast['name'])

    block = fn.append_basic_block('entry')
    builder = ir.IRBuilder(block)

    [env_ptr, arg] = fn.args
    env_type = ir.LiteralStructType([type_to_ir(e['vtype']) for e in ast['env']])
    env_ptr = builder.bitcast(env_ptr, ir.PointerType(env_type), '.env')
    def get_env_value(i, e):
        indices = [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)]
        ptr = builder.gep(env_ptr, indices, name='.env.' + e['name'])
        return builder.load(ptr, name=e['name'])
    env_values = [get_env_value(i, e) for i, e in enumerate(ast['env'])]
    scope_values = [(x.name, x) for x in env_values + [arg]]

    scope = Scope()
    for name, value in scope_values:
        scope = scope.add(name, value)

    value, _ = generate_expression(ast['body'], builder, scope)

    builder.ret(value)

def generate_main(main_body):
    fn = ir.Function(module, ir.FunctionType(ir.IntType(32), ()), name='main')

    block = fn.append_basic_block('entry')
    builder = ir.IRBuilder(block)

    value, _ = generate_expression(main_body, builder, Scope())
    builder.ret(value)

def find_fn(name):
    fn, *tail = [x for x in module.functions if x.name == name]
    return fn

def compiler(ast):
    for external in ast['externals']:
        declare_external(external)
    for fn in ast['fns']:
        declare_fn(fn)
    for fn in ast['fns']:
        generate_fn_body(fn)

    generate_main(ast['main'])

    return str(module)


if __name__ == '__main__':
    import json
    import sys

    ast = json.load(sys.stdin)
    llvm_ir = compiler(ast)
    sys.stdout.write(llvm_ir)
