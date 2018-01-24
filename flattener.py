#!/usr/bin/env python3

class Scope:
    def __init__(self, parent, args):
        expressions = {arg: {"type": "arg"} for arg in args}
        self.expressions = expressions
        self.parent = parent

    @classmethod
    def root(cls, fns):
        expressions = {name: {"type": "fn", "args": fn["args"]} for name, fn in fns.items()}
        return cls(None, expressions)

    def copy(self):
        return self.__class__(self.parent, self.expressions.copy())

    def add(self, name, val):
        new = self.copy()
        new.expressions.update({name: val})
        return new

    def find(self, name):
        expression = self.expressions.get(name)
        if expression is not None: return expression

        if self.parent is None: return None
        return self.parent.find(name)

def create_fn(ast, fns, scope):
    name = ast["name"]
    args = ast["args"]

    child_scope = Scope(scope, args)
    child_ast, fns, _, used_scope = create_expression(ast["body"], fns, child_scope)

    used_scope = [x for x in used_scope if x not in args]
    args = used_scope + args

    fns[name] = {
        "args": args,
        "body": child_ast
    }
    scope = scope.add(name, {
        "type": "fn",
        "args": args
    })
    return (None, fns, scope, [])

def create_val(ast, fns, scope):
    name = ast["name"]
    ast = {
        "type": "val",
        "name": name,
        "body": ast["body"]
    }
    scope = scope.add(name, {"type": "val"})
    return (ast, fns, scope, [])

def create_def(ast, fns, scope):
    if ast["args"]: return create_fn(ast, fns, scope)
    else: return create_val(ast, fns, scope)

def create_integer(ast, fns, scope):
    return (ast, fns, scope, [])

def create_call(ast, fns, scope):
    used_scope = [ast["name"]]
    for arg in ast["args"]:
        child_ast, fns, _, child_used_scope = create_expression(arg, fns, scope)
        used_scope.extend(child_used_scope)
    return (ast, fns, scope, used_scope)

def create_block(ast, fns, scope):
    used_scope = []
    new_body = []
    child_scope = scope
    for child in ast["body"]:
        child_ast, fns, child_scope, child_used_scope = create_expression(child, fns, child_scope)
        used_scope.extend(child_used_scope)
        new_body.append(child_ast)
    new_body = [x for x in new_body if x]
    ast["body"] = new_body

    return (ast, fns, scope, used_scope)

def create_expression(ast, fns, scope):
    if ast["type"] == "def":
        return create_def(ast, fns, scope)
    elif ast["type"] == "integer":
        return create_integer(ast, fns, scope)
    elif ast["type"] == "call":
        return create_call(ast, fns, scope)
    elif ast["type"] == "block":
        return create_block(ast, fns, scope)
    else:
        raise ValueError("Wrong type: " + str(ast["type"]))


internal_fns = {
    "add": {
        "args": ["lhs", "rhs"],
        "body": "internal"
    }
}
root_scope = Scope.root(internal_fns)

main_ast, all_fns, _, used_scope_main = create_expression(root_ast, internal_fns, root_scope)

root_flat = {
    "fns": all_fns,
    "main": main_ast
}


if __name__ == "__main__":
    import json
    import sys

    ast = json.load(sys.stdin)
    normalized_ast = normalize_ast(ast)
    json.dump(normalized_ast, sys.stdout, indent=4)
    sys.stdout.write("\n")
