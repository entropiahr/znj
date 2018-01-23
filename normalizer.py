#!/usr/bin/env python3
"""
This module translates pure ast to ast with normalized functions.

Normalized functions are functions that explicitly take environment arguments
through "env".

Also, this module transforms "def" that has no "args" to "def_name", and "def"
with "args" to "fn_def".
"""

class ScopeName:
    def __init__(self, type, name):
        self.type = type
        self.name = name
        self.env = []

    def copy(self):
        new = self.__class__(self.type, self.name)
        new.env = self.env.copy()
        return new

    def add_env(self, env):
        self.env = [{"type": "call", "name": env_arg, "args": []} for env_arg in env]


class Scope:
    def __init__(self, parent=None):
        if parent is None:
            self.snames = []
            return

        self.snames = [sname for sname in parent.copy().snames if sname.type == "fn"]

    def copy(self):
        new = self.__class__()
        new.snames = [sname.copy() for sname in self.snames]
        return new

    def add_fns(self, *snames):
        new = self.copy()
        new.snames.extend([ScopeName("fn", sname) for sname in snames])
        return new

    def add_fn_env(self, name, env):
        new = self.copy()
        for sname in new.snames:
            if sname.name == name:
                sname.add_env(env)
        return new

    def add_names(self, *snames):
        new = self.copy()
        new.snames.extend([ScopeName("name", sname) for sname in snames])
        return new

    def find(self, name):
        res = [sname for sname in self.snames if sname.name == name]
        if res: return res[-1]
        return None


def normalize_def_fn(ast, scope):
    scope = scope.add_fns(ast["name"])

    child_scope = Scope(scope).add_names(*ast["args"])
    body_ast, _, used = normalize_expression(ast["body"], child_scope)

    scope = scope.add_fn_env(ast["name"], used)
    ast["env"] = used

    return (ast, scope, [])

def normalize_def_name(ast, scope):
    body, _, used = normalize_expression(ast["body"], scope)

    ast = {
        "type": "def_name",
        "name": ast["name"],
        "body": body
    }
    scope = scope.add_names(ast["name"])
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
        env = scope_name.env
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
    scope = Scope().add_fns("add")
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
