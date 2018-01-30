#!/usr/bin/env python3
"""
This module translates pure ast to ast with normalized functions.

Normalized functions with their bodies are in "fn" field, while their definition
is with the rest of the code in "main" field.

Also, this module transforms "def" that has no "args" to "def_name", and "def"
with "args" to "def_fn_simple" or "def_fn_env".

"def_fn_simple" can be called by only supplying "args" while "def_fn_env" must
be called with its "env".
"""


class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.fns = None if parent else []
        self.asts = []
        self.loans = []

    def copy(self):
        new = self.__class__(self.parent)
        new.asts = self.asts.copy()
        new.loans = self.loans.copy()
        if new.parent is None:
            new.fns = new.fns.copy()
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

    def find(self, name, type):
        match = lambda ast: ast["name"] == name and type_infer(ast["vtype"], type)
        results = [ast for ast in self.asts if match(ast)]
        if results:
            ast = results[-1]
            ast["vtype"] = type_infer(ast["vtype"], type)
            return (ast, self)

        if self.parent is None:
            raise ValueError("Can't find name: " + name)

        ast, new_parent = self.parent.find(name, type)

        if ast["type"] == "internal":
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
        raise ValueError("Types don't match: " + str(a) + " " + str(b))

    return result

def type_unknown():
    return "unknown"

def type_fn(arg_types, ret_type):
    type = ret_type
    for arg_type in arg_types:
        type = ["->", arg_type, type]
    return type


def normalize_def(ast, scope, requested_type):
    arg_names = ast["args"]
    args = [{"type": "arg", "name": name, "vtype": type_unknown()} for name in arg_names] 

    body_scope = Scope(scope)
    for arg in args:
        body_scope = body_scope.add(arg)

    body, body_scope = normalize_expression(ast["body"], body_scope, type_unknown())
    scope = body_scope.parent

    ret_type = body["vtype"]
    type = type_fn([arg["vtype"] for arg in args], ret_type)
    type = type_validate(type, requested_type)

    is_function = type[0] == "->"

    if is_function:
        loan_calls = []
        for l in body_scope.loans:
            l_scope = Scope(scope)
            l, l_scope = normalize_name({"type": "name", "name": l["name"]}, l_scope, l["vtype"])
            loan_calls.append(l)
            scope = l_scope.parent

        ast = {
            "type": "def_fn",
            "name": ast["name"],
            "env": loan_calls,
            "vtype": type
        }
        fn = {
            "name": ast["name"],
            "env": [{"type": "env_arg", "name": l["name"], "vtype": l["vtype"]} for l in loan_calls],
            "args": args,
            "ret_type": ret_type,
            "body": body
        }

        scope = scope.add_fn(fn)
    else:
        ast = {
            "type": "def_name",
            "name": ast["name"],
            "vtype": type,
            "body": body
        }

    scope = scope.add(ast)

    return (ast, scope)

def normalize_name(ast, scope, type):
    scope_ast, scope = scope.find(ast["name"], type)

    if scope_ast["type"] == "def_fn":
        ast["env"] = scope_ast["env"]

    ast["vtype"] = type_validate(scope_ast["vtype"], type)

    return (ast, scope)

def normalize_call(ast, scope, requested_type):
    assert len(ast["args"]) >= 2
    caller, *args = ast["args"]

    caller_type = requested_type
    for _ in args:
        caller_type = ["->", type_unknown(), caller_type]

    caller_scope = Scope(scope)
    caller, caller_scope = normalize_expression(caller, caller_scope, caller_type)
    scope = caller_scope.parent
    caller_type = caller["vtype"]

    type = caller_type
    arg_types = []
    for _ in args:
        if type[0] != "->":
            raise ValueError("Passed more arguments then needed in: " + call["name"])
        arg_types.append(type[1])
        type = type[2]
    type = type_validate(type, requested_type)

    new_args = []
    for arg, arg_type in zip(args, arg_types):
        arg_scope = Scope(scope)
        arg, arg_scope = normalize_expression(arg, arg_scope, arg_type)
        scope = arg_scope.parent
        new_args.append(arg)

    ast["args"] = [caller] + new_args
    ast["vtype"] = type

    return (ast, scope)

def normalize_block(ast, scope, type):
    body = []
    child_scope = Scope(scope)
    for i, child in enumerate(ast["body"]):
        is_last = i == len(ast["body"]) -1
        child_type = type if is_last else type_unknown()
        child, child_scope = normalize_expression(
            child, child_scope, child_type
        )
        body.append(child)
    scope = child_scope.parent

    ast["vtype"] = body[-1]["vtype"]
    ast["body"] = body
    return (ast, scope)

def normalize_integer(ast, scope, type):
    ast["vtype"] = type_validate(["Int"], type)
    return (ast, scope)

def normalize_instruction(ast, scope, type):
    if ast["name"] == "add":
        args = []
        for arg in ast["args"]:
            arg_scope = Scope(scope)
            arg, arg_scope = normalize_expression(arg, arg_scope, ["Int"])
            scope = arg_scope.parent
            args.append(arg)
        ast["vtype"] = type_validate(["Int"], type)
        ast["args"] = args
        return (ast, scope)
    else:
        raise ValueError("Unknown instruction: " + ast["name"])

def normalize_expression(ast, scope, type):
    if ast["type"] == "def":
        return normalize_def(ast, scope, type)
    elif ast["type"] == "name":
        return normalize_name(ast, scope, type)
    elif ast["type"] == "call":
        return normalize_call(ast, scope, type)
    elif ast["type"] == "block":
        return normalize_block(ast, scope, type)
    elif ast["type"] == "integer":
        return normalize_integer(ast, scope, type)
    elif ast["type"] == "instruction":
        return normalize_instruction(ast, scope, type)
    else:
        raise ValueError("Wrong ast type: " + str(ast["type"]))

def normalize_ast(ast):
    scope = Scope()
    ast, scope = normalize_expression(ast, scope, ["Int"])

    return {
        "fns": scope.fns,
        "main": ast
    }


if __name__ == "__main__":
    import json
    import sys

    ast = json.load(sys.stdin)
    normalized_ast = normalize_ast(ast)
    json.dump(normalized_ast, sys.stdout, indent=4)
    sys.stdout.write("\n")
