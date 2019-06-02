#!/usr/bin/env python3

"""
This module translates simplified ast to ast with normalized functions.

Every function is translated to closure object. Closure object is a struct with
normalized function and function environment.

Normalized function takes two arguments. First argument is environment and
second argument is just a single argument. Function can return type or another
function as a closure.

Normalized functions with their bodies are in "fn" field, while their closures
are created in a function that uses them with the rest of the variables.

Also, this module transforms "def" that has no "args" to "def_name", and "def"
with "args" to "def_fn".

Every function must be called as closure by supplying environment as a first
argument and a single argument as a second argument.
"""


class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.externals = None if parent else []
        self.fns = None if parent else []
        self.asts = []
        self.loans = []

    def copy(self):
        new = self.__class__(self.parent)
        new.asts = self.asts.copy()
        new.loans = self.loans.copy()
        if new.parent is None:
            new.fns = self.fns.copy()
            new.externals = self.externals.copy()
        return new

    def add(self, ast):
        new = self.copy()
        new.asts.append(ast)
        return new

    def add_fn(self, fn):
        new = self.copy()
        if new.parent:
            new.parent = new.parent.add_fn(fn)
        else:
            new.fns.append(fn)
        return new

    def add_external(self, external):
        new = self.copy()
        if new.parent:
            new.parent = new.parent.add_external(external)
        else:
            new.externals.append(external)
        return new

    def find(self, name, type):
        match = lambda ast: ast['name'] == name and type_infer(ast['vtype'], type)
        results = [ast for ast in self.asts if match(ast)]
        if results:
            ast = results[-1]
            ast['vtype'] = type_infer(ast['vtype'], type)
            return (ast, self)

        if self.parent is None:
            raise ValueError(f"Can't find name: {repr(name)}")

        ast, new_parent = self.parent.find(name, type)

        if ast['type'] == 'internal':
            return (ast, self)

        new = self.copy()
        new.parent = new_parent
        new.loans.append(ast)

        return (ast, new)


def type_infer(a, b):
    if a == type_unknown(): return b
    if b == type_unknown(): return a

    a_name, *a_args = a
    b_name, *b_args = b

    if a_name != b_name: return None
    if len(a_args) != len(b_args): return None

    return [a_name] + [type_infer(a, b) for a, b in zip(a_args, b_args)]

def type_validate(a, b):
    result = type_infer(a, b)
    if result is None:
        raise ValueError(f"Types don't match: {a} {b}")

    return result

def type_unknown():
    return 'unknown'

def type_function_split(type):
    if type == type_unknown(): return (type_unknown(), type_unknown())
    if type[0] != '->': raise ValueError(f"Type {type} is not a functinon.")
    return (type[1], type[2])

def type_function_create(arg_type, ret_type):
    return ['->', arg_type, ret_type]


def normalize_def(ast, scope, requested_type):
    body_scope = Scope(scope)

    body, body_scope = normalize_expression(ast['body'], body_scope, requested_type)
    scope = body_scope.parent

    ast['body'] = body
    ast['vtype'] = body['vtype']

    scope = scope.add(ast)

    return (ast, scope)

def normalize_fn(ast, scope, requested_type):
    arg_type, ret_type = type_function_split(requested_type)
    arg = {'type': 'arg', 'name': ast['arg'], 'vtype': arg_type}

    body_scope = Scope(scope).add(arg)
    body, body_scope = normalize_expression(ast['body'], body_scope, ret_type)
    scope = body_scope.parent

    arg_type = arg['vtype'] # uses mutability!
    ret_type = body['vtype']
    type = type_validate(requested_type, type_function_create(arg_type, ret_type))

    loan_calls = []
    for l in body_scope.loans:
        l_scope = Scope(scope)
        l, l_scope = normalize_name({'type': 'name', 'name': l['name']}, l_scope, l['vtype'])
        loan_calls.append(l)
        scope = l_scope.parent

    fn = {
        'name': ast['name'] + '.fn',
        'env': [{'type': 'env_arg', 'name': l['name'], 'vtype': l['vtype']} for l in loan_calls],
        'arg': arg,
        'ret_type': ret_type,
        'body': body,
        'external': False,
    }
    scope = scope.add_fn(fn)

    ast['env'] = loan_calls
    ast['vtype'] = type
    del ast['body']
    del ast['arg']

    return (ast, scope)

def normalize_name(ast, scope, type):
    scope_ast, scope = scope.find(ast['name'], type)

    if scope_ast['type'] == 'def_fn':
        ast['env'] = scope_ast['env']

    ast['vtype'] = type_validate(scope_ast['vtype'], type)

    return (ast, scope)

def normalize_call(ast, scope, requested_type):
    call_type = type_function_create(type_unknown(), requested_type)

    call_scope = Scope(scope)
    call, call_scope = normalize_expression(ast['call'], call_scope, call_type)
    scope = call_scope.parent

    arg_type, type = type_function_split(call['vtype'])

    arg_scope = Scope(scope)
    arg, arg_scope = normalize_expression(ast['arg'], arg_scope, arg_type)
    scope = arg_scope.parent

    ast['vtype'] = type_validate(requested_type, type)

    ast['call'] = call
    ast['arg'] = arg

    return (ast, scope)

def normalize_block(ast, scope, type):
    body = []
    child_scope = Scope(scope)
    for i, child in enumerate(ast['body']):
        is_last = i == len(ast['body']) -1
        child_type = type if is_last else type_unknown()
        child, child_scope = normalize_expression(
            child, child_scope, child_type
        )
        body.append(child)
    scope = child_scope.parent

    ast['vtype'] = body[-1]['vtype']
    ast['body'] = body
    return (ast, scope)

def normalize_integer(ast, scope, type):
    ast['vtype'] = type_validate(['Int'], type)
    return (ast, scope)

def normalize_instruction(ast, scope, type):
    if ast['instruction'] == 'add':
        args = []
        for arg in ast['args']:
            arg_scope = Scope(scope)
            arg, arg_scope = normalize_expression(arg, arg_scope, ['Int'])
            scope = arg_scope.parent
            args.append(arg)
        ast['vtype'] = type_validate(['Int'], type)
        ast['args'] = args
        return (ast, scope)
    else:
        raise ValueError(f"Unknown instruction: {ast['name']}")

def normalize_external(ast, scope, type):
    args = []
    for arg in ast['args']:
        arg_scope = Scope(scope)
        arg, arg_scope = normalize_expression(arg, arg_scope, ['Int'])
        scope = arg_scope.parent
        args.append(arg)

    external = {
        'name': ast['name'],
        'vtype': ast['vtype'],
        'args': ast['args'],
    }
    scope = scope.add_external(external)

    ast = {
        'type': 'external',
        'name': ast['name'],
        'vtype': ['Int'],
        'args': ast['args'],
    }
    return (ast, scope)

def normalize_expression(ast, scope, type):
    if ast['type'] == 'def':
        return normalize_def(ast, scope, type)
    elif ast['type'] == 'fn':
        return normalize_fn(ast, scope, type)
    elif ast['type'] == 'name':
        return normalize_name(ast, scope, type)
    elif ast['type'] == 'call':
        return normalize_call(ast, scope, type)
    elif ast['type'] == 'block':
        return normalize_block(ast, scope, type)
    elif ast['type'] == 'integer':
        return normalize_integer(ast, scope, type)
    elif ast['type'] == 'instruction':
        return normalize_instruction(ast, scope, type)
    elif ast['type'] == 'external':
        return normalize_external(ast, scope, type)
    else:
        raise ValueError(f"Wrong ast type: {ast['type']}")

def normalizer(ast):
    scope = Scope()
    ast, scope = normalize_expression(ast, scope, ['Int'])

    return {
        'externals': scope.externals,
        'fns': scope.fns,
        'main': ast,
    }


if __name__ == '__main__':
    import json
    import sys

    ast = json.load(sys.stdin)
    normalized_ast = normalizer(ast)
    json.dump(normalized_ast, sys.stdout, indent=2)
    sys.stdout.write('\n')
