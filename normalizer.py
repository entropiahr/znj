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
        self.asts = []
        self.borrowed = []

        #if parent is None:
        #    self.asts = []
        #    return
        #self.asts = [ast for ast in parent.copy().asts if ast["type"] == "def_fn_simple"]

    def copy(self):
        new = self.__class__(self.parent)
        new.asts = self.asts.copy()
        new.borrowed = self.borrowed.copy()
        return new

    def add(self, ast):
        new = self.copy()
        new.asts.append(ast)
        return new

    def find(self, name):
        res = [ast for ast in self.asts if ast["name"] == name]
        if res: return (res[-1], self)

        if self.parent is None:
            raise ValueError("Can't find name: " + name)

        ast, new_parent = self.parent.find(name)

        if ast["type"] == "def_fn_simple":
            return (ast, self)

        new = self.copy()
        new.parent = new_parent
        new.borrowed.append(ast)

        return (ast, new)


def type_infer(a, b):
    if a == type_empty(): return b
    if b == type_empty(): return a

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

def type_empty():
    return ["a"]

def type_fn(arg_types, ret_type):
    type = ret_type
    for arg_type in arg_types:
        type = ["->", arg_type, type]
    return type

def normalize_def(ast, scope, requested_type):
    arg_names = ast["args"]
    args = [{"type": "def_name", "name": name, "vtype": type_empty()} for name in arg_names] 

    body_scope = Scope(scope)
    for arg in args:
        body_scope = body_scope.add(arg)

    body, body_scope, body_fns = normalize_expression(ast["body"], body_scope, type_empty())
    scope = body_scope.parent

    type = type_fn([arg["vtype"] for arg in args], body["vtype"])
    type = type_validate(type, requested_type)

    is_function = type[0] == "->"

    fns = body_fns

    if is_function:
        ast = {
            "type": "def_fn_simple",
            "name": ast["name"],
            "vtype": type
        }
        fn = {
            "name": ast["name"],
            "args": args,
            "vtype": type,
            "body": body
        }

        env = body_scope.borrowed
        if env:
            env_call = [{"type": "call", "name": e["name"], "args": []} for e in env]
            ast["type"] = "def_fn_env"
            ast["env"] = env_call

            env_def = [{"type": "def_name", "name": e["name"], "vtype": e["vtype"]} for e in env]
            fn["env"] = env_def

        fns = fns + [fn]
    else:
        ast = {
            "type": "def_name",
            "name": ast["name"],
            "vtype": type,
            "body": body
        }

    scope = scope.add(ast)

    return (ast, scope, fns)

def normalize_integer(ast, scope, type):
    ast["vtype"] = type_validate(["Int"], type)
    return (ast, scope, [])

def normalize_call(ast, scope, requested_type):
    scope_ast, scope = scope.find(ast["name"])

    type = scope_ast["vtype"]
    arg_types = []
    for _ in ast["args"]:
        if type[0] != "->":
            raise ValueError("Passed more arguments then needed in: " + ast["name"])
        arg_types.append(type[1])
        type = type[2]
    type = type_validate(type, requested_type)

    args = []
    fns = []
    for arg, arg_type in zip(ast["args"], arg_types):
        arg_scope = Scope(scope)
        arg, arg_scope, arg_fns = normalize_expression(arg, arg_scope, arg_type)
        scope = arg_scope.parent
        args.append(arg)
        fns.extend(arg_fns)

    ast["args"] = args
    ast["vtype"] = type

    if scope_ast.get("env"):
        ast["env"] = ast["name"] + ".env"

    return (ast, scope, fns)

def normalize_block(ast, scope, type):
    body = []
    fns = []
    child_scope = scope
    for i, child in enumerate(ast["body"]):
        is_last = i == len(ast["body"]) -1
        child_type = type if is_last else ["a"]
        child, child_scope, child_fns = normalize_expression(
            child, child_scope, child_type
        )
        body.append(child)
        fns.extend(child_fns)

    ast["vtype"] = body[-1]["vtype"]
    ast["body"] = body
    return (ast, scope, fns)

def normalize_expression(ast, scope, type):
    if ast["type"] == "def":
        return normalize_def(ast, scope, type)
    elif ast["type"] == "integer":
        return normalize_integer(ast, scope, type)
    elif ast["type"] == "call":
        return normalize_call(ast, scope, type)
    elif ast["type"] == "block":
        return normalize_block(ast, scope, type)
    else:
        raise ValueError("Wrong ast type: " + str(ast["type"]))

def normalize_ast(ast):
    add = {
        "type": "def_fn_simple",
        "name": "add",
        "vtype": ["->", ["Int"], ["->", ["Int"], ["Int"]]]
    }
    scope = Scope().add(add)
    ast, _, fns = normalize_expression(ast, scope, ["Int"])

    return {
        "fns": fns,
        "main": ast
    }


if __name__ == "__main__":
    import json
    import sys

    ast = json.load(sys.stdin)
    normalized_ast = normalize_ast(ast)
    json.dump(normalized_ast, sys.stdout, indent=4)
    sys.stdout.write("\n")
