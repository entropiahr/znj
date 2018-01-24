#!/usr/bin/env python3
"""
This module translates pure ast to ast with normalized functions.

Normalized functions are functions that explicitly take environment arguments
through "env".

Also, this module transforms "def" that has no "args" to "def_name", and "def"
with "args" to "def_fn".
"""

class ScopeName:
    def __init__(self, type, name, env=None):
        self.type = type
        self.name = name
        self.env = env

    def get_env(self):
        if self.env is None: return None
        return [{"type": "call", "name": e, "args": []} for e in self.env]


class Scope:
    def __init__(self, parent=None):
        if parent is None:
            self.snames = []
            return

        self.snames = [sname for sname in parent.copy().snames if sname.type == "fn"]

    def copy(self):
        new = self.__class__()
        new.snames = self.snames.copy()
        return new

    def add(self, ast):
        new = self.copy()

        if ast["type"] == "def_name":
            sname = ScopeName("name", ast["name"])
        elif ast["type"] == "def_fn":
            sname = ScopeName("fn", ast["name"], ast.get("env"))
        else:
            raise ValueError("Wrong type in scope: " + str(ast["type"]))

        new.snames.append(sname)
        return new

    def find(self, name):
        res = [sname for sname in self.snames if sname.name == name]
        if res: return res[-1]
        return None


def normalize_def_fn(ast, scope):
    child_scope = Scope(scope)
    for arg in ast["args"]:
        child_scope = child_scope.add({"type": "def_name", "name": arg})
    body_ast, _, used = normalize_expression(ast["body"], child_scope)

    ast["type"] = "def_fn"
    ast["env"] = used
    scope = scope.add(ast)

    return (ast, scope, [])

def normalize_def_name(ast, scope):
    body, _, used = normalize_expression(ast["body"], scope)

    ast = {
        "type": "def_name",
        "name": ast["name"],
        "body": body
    }
    scope = scope.add(ast)
    return (ast, scope, used)

def normalize_def(ast, scope):
    if ast["args"]: return normalize_def_fn(ast, scope)
    else: return normalize_def_name(ast, scope)

def normalize_integer(ast, scope):
    return (ast, scope, [])

def normalize_call(ast, scope):
    scope_name = scope.find(ast["name"])
    if scope_name:
        used = []
        env = scope_name.get_env()
    else:
        used = [ast["name"]]
        env = None

    args = []
    for arg in ast["args"]:
        arg, _, arg_used = normalize_expression(arg, scope)
        args.append(arg)
        used.extend(arg_used)
    ast["args"] = args

    if env:
        env_args = []
        for env_arg in env:
            env_arg, _, env_arg_used = normalize_expression(env_arg, scope)
            env_args.append(env_arg)
            used.extend(env_arg_used)
        ast["env"] = env_args

    return (ast, scope, used)

def normalize_block(ast, scope):
    body = []
    used = []
    child_scope = scope
    for child in ast["body"]:
        child, child_scope, child_used = normalize_expression(child, child_scope)
        body.append(child)
        used.extend(child_used)

    ast["body"] = body
    return (ast, scope, used)

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
    scope = Scope().add({"type": "def_fn", "name": "add"})
    ast, _, used = normalize_expression(ast, scope)

    if used:
        raise ValueError("Can't find names: " + ", ".join(used))

    return ast


if __name__ == "__main__":
    import json
    import sys

    ast = json.load(sys.stdin)
    normalized_ast = normalize_ast(ast)
    json.dump(normalized_ast, sys.stdout, indent=4)
    sys.stdout.write("\n")
