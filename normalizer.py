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
        if parent is None:
            self.asts = []
            return

        self.asts = [ast for ast in parent.copy().asts if ast["type"] == "def_fn_simple"]

    def copy(self):
        new = self.__class__()
        new.asts = self.asts.copy()
        return new

    def add(self, ast):
        new = self.copy()
        new.asts.append(ast)
        return new

    def find(self, name):
        res = [ast for ast in self.asts if ast["name"] == name]
        if res: return res[-1]
        return None


def normalize_def_fn(ast, scope):
    args = ast["args"]

    child_scope = Scope(scope)
    for arg in args:
        child_scope = child_scope.add({"type": "def_name", "name": arg})
    body, _, env, body_fns = normalize_expression(ast["body"], child_scope)

    if env:
        ast = {
            "type": "def_fn_env",
            "name": ast["name"],
            "env": [{"type": "call", "name": e, "args": []} for e in env]
        }
    else:
        ast = {
            "type": "def_fn_simple",
            "name": ast["name"]
        }

    scope = scope.add(ast)

    used = [e for e in env if scope.find(e) == None]

    fn = {
        "name": ast["name"],
        "args": args,
        "env": env,
        "body": body
    }
    fns = body_fns + [fn]

    return (ast, scope, used, fns)

def normalize_def_name(ast, scope):
    body, _, used, body_fns = normalize_expression(ast["body"], scope)

    ast = {
        "type": "def_name",
        "name": ast["name"],
        "body": body
    }
    scope = scope.add(ast)
    return (ast, scope, used, body_fns)

def normalize_def(ast, scope):
    if ast["args"]: return normalize_def_fn(ast, scope)
    else: return normalize_def_name(ast, scope)

def normalize_integer(ast, scope):
    return (ast, scope, [], [])

def normalize_call(ast, scope):
    scope_ast = scope.find(ast["name"])
    if scope_ast:
        used = []
        env = scope_ast.get("env")
    else:
        used = [ast["name"]]
        env = None

    args = []
    fns = []
    for arg in ast["args"]:
        arg, _, arg_used, arg_fns = normalize_expression(arg, scope)
        args.append(arg)
        used.extend(arg_used)
        fns.extend(arg_fns)
    ast["args"] = args

    if env:
        ast["env"] = ast["name"] + ".env"

    return (ast, scope, used, fns)

def normalize_block(ast, scope):
    body = []
    used = []
    fns = []
    child_scope = scope
    for child in ast["body"]:
        child, child_scope, child_used, child_fns = normalize_expression(child, child_scope)
        body.append(child)
        used.extend(child_used)
        fns.extend(child_fns)

    ast["body"] = body
    return (ast, scope, used, fns)

def normalize_expression(ast, scope):
    if ast["type"] == "def":
        return normalize_def(ast, scope)
    elif ast["type"] == "integer":
        return normalize_integer(ast, scope)
    elif ast["type"] == "call":
        return normalize_call(ast, scope)
    elif ast["type"] == "block":
        return normalize_block(ast, scope)
    else:
        raise ValueError("Wrong type: " + str(ast["type"]))

def normalize_ast(ast):
    scope = Scope().add({"type": "def_fn_simple", "name": "add"})
    ast, _, used, fns = normalize_expression(ast, scope)

    if used:
        raise ValueError("Can't find names: " + ", ".join(used))

    return {
        "fns": fns,
        "main": {
            "name": "main",
            "args": [],
            "env": [],
            "body": ast
        }
    }


if __name__ == "__main__":
    import json
    import sys

    ast = json.load(sys.stdin)
    normalized_ast = normalize_ast(ast)
    json.dump(normalized_ast, sys.stdout, indent=4)
    sys.stdout.write("\n")
