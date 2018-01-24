#!/usr/bin/env python3

from llvmlite import ir

int_type = ir.IntType(32)

module = ir.Module()
module.triple = "x86_64-unknown-linux-gnu"

class Expression:
    def __init__(self, context, used_context, call):
        self.context = context
        self.used_context = used_context
        self.call = call

    @classmethod
    def integer(cls, context, value):
        return cls(context, dict(), lambda builder, args: ir.Constant(int_type, value))


class Context:
    def __init__(self, parent, expressions):
        self.expressions = expressions
        self.parent = parent

    @classmethod
    def root(cls, expressions):
        return cls(None, expressions)

    def copy(self):
        parent = self.parent.copy() if self.parent is not None else None
        expressions = self.expressions.copy()
        return self.__class__(parent, expressions)

    def add(self, name, call):
        new = self.copy()
        new.expressions.update({name: call})
        return new

    def find(self, name):
        expression = self.expressions.get(name)
        if expression is not None: return expression
        if self.parent is None: return None
        return self.parent.find(name)

def create_def(ast, context):
    args = ast["args"]
    name = ast["name"]
    body = ast["body"]
    if args or name == "main":
        context_args = [(name, call) for name, call in context.expressions.items() if name == "val_x"]
        context_arg_names = [name for name, _ in context_args]
        arg_names = context_arg_names + ast["args"]

        base_arg_types = [int_type for _ in arg_names]
        base_args = tuple(Argument())
        function_type = ir.FunctionType(int_type, arg_types)

        function = ir.Function(module, type, ast["name"])

        arg_calls = map(lambda arg: lambda _builder, _args: arg, function.args)
        args = dict(zip(arg_names, arg_calls))

        child_context = Context(context, args)
        child_expression = create_expression(body, child_context)
        used_context = child_expression.used_context

        block = function.append_basic_block("entry")
        child_builder = ir.IRBuilder(block)
        child_builder.ret(child_expression.call(child_builder, []))

        def call(builder, args):
            context_arg_values = [call(builder, []) for _, call in context_args]
            return builder.call(function, context_arg_values + args)
    else:
        child_expression = create_expression(body, context)
        used_context = child_expression.used_context
        call = child_expression.call

    if used_context: print(used_context)
    context = context.add(name, call)
    return Expression(context, used_context, call)

def create_block(ast, context):
    body = ast["body"]
    if not body: raise ValueError("body mustn't be empty!")

    child_context = context
    for child in body:
        child_expression = create_expression(child, child_context)
        child_context = child_expression.context
        last_expression = child_expression

    last_expression.context = context
    return last_expression

def create_integer(ast, context):
    return Expression.integer(context, ast["value"])

def create_call(ast, context):
    this_call = context.find(ast["name"])
    arg_expressions = [create_expression(arg, context) for arg in ast["args"]]

    used_context = {ast["name"]: this_call}
    for arg_expression in arg_expressions:
        used_context.update(arg_expression.used_context)

    arg_calls = [arg_expression.call for arg_expression in arg_expressions]
    def call(builder, args):
        args = [arg_call(builder, []) for arg_call in arg_calls]
        return this_call(builder, args)

    return Expression(context, used_context, call)

def create_expression(ast, context):
    t = ast["type"]

    if t == "def":
        return create_def(ast, context)
    elif t == "integer":
        return create_integer(ast, context)
    elif t == "call":
        return create_call(ast, context)
    elif t == "block":
        return create_block(ast, context)
    else:
        raise ValueError("Wrong type: " + str(ast["type"]))

def unused1():
    root_context = Context.root({
        "add": lambda builder, args: builder.add(args[0], args[1])
    })

    main = ir.Function(module, ir.FunctionType(int_type, ()), name="main")
    block = main.append_basic_block("entry")
    builder = ir.IRBuilder(block)

    root_expression = create_expression(root_ast, root_context)
    result = root_expression.call(builder, [])
    builder.ret(result)

def unused2():
    print("\n\n=======================================\n\n")
    print(module)
    with open("test.ll", "w") as output:
        output.write(str(module))

def unused3():
    my_add = ir.Function(module, ir.FunctionType(int_type, (int_type, int_type)), name="my_add")

    block = func.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)
    a, b, c = func.args
    result = builder.add(a, b, name="res")
    result = builder.add(result, c, name="res")
    builder.ret(result)

    main = ir.Function(module, ir.FunctionType(int_type, ()), name="main")
    block = main.append_basic_block()
    builder.position_at_start(block)
    first = builder.alloca(int_type, name="first")
    builder.store(ir.Constant(int_type, 11), first)
    func_ptr = builder.alloca(my_add.type.as_pointer(), name="func_ptr")
    builder.store(my_add, func_ptr)
    result = builder.call(func, (ir.Constant(int_type, 23), ir.Constant(int_type, 23), ir.Constant(int_type, 2)))
    builder.ret(result)


def generate_fn(fn):
    arg_types = tuple(int_type for x in fn["args"])
    function = ir.Function(module, ir.FunctionType(int_type, arg_types), name=fn["name"])
    function.args = tuple(ir.Argument(function, t, n) for n, t in zip(fn["args"], arg_types))

    block = function.append_basic_block("entry")
    builder = ir.IRBuilder(block)

    builder.ret(ir.Constant(int_type, 0))

def generate_ast(ast):
    for fn in ast["fns"]:
        generate_fn(fn)

    generate_fn({"name": "main", "args": [], "env": []})

    return str(module)


if __name__ == "__main__":
    import json
    import sys

    ast = json.load(sys.stdin)
    llvm_ir = generate_ast(ast)
    sys.stdout.write(llvm_ir)
