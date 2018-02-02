#!/usr/bin/env python3

"""
This module translates parsed ast to simplified ast.

Nodes (with exceptions) will have "name" field.

Nodes without "name": "integer"

"def" is translated so that it doesn't have any arguments. A new type is added,
called "fn". "fn" is a function that takes exactly one "arg". If previous "def"
took more than one argument in "args", the function is nested n times, where n
is number of arguments.

Example input:

{
    "type": "def",
    "name": "foo",
    "args": ["arg1", "arg2"],
    "body": {"type": "integer", "value": 10}
}

Example output:

{
    "type": "def",
    "name": "foo",
    "body": {
        "type": "fn",
        "name": "foo",
        "arg": "arg1",
        "body": {
            "type": "fn",
            "name": "foo.1",
            "arg": "arg2",
            "body": {"type": "integer", "value": 10}
        }
    }
}

Every "call" is translated so that there are only "call" and a single "arg".
They are translated to nested calls recursively from left to right.

Example input (parent sent name "parent"):

{
    "type": "call",
    "args": [
        {"type": "name", "name": "foo"},
        {"type": "name", "name": "arg1"},
        {"type": "name", "name": "arg2"},
        {"type": "name", "name": "arg3"}
    ]
}

Example output:

{
    "type": "call",
    "name": "parent",
    "call": {
        "type": "call",
        "name": "parent.call",
        "call": {
            "type": "call",
            "name": "parent.call.call",
            "call": {"type": "name", "name": "foo"},
            "arg": {"type": "name", "name": "arg1"}
        }
        "arg": {"type": "name", "name": "arg2"}
    }
    "arg": {"type": "name", "name": "arg2"}
}
"""

def simplify_def(ast, name):
    args = ast["args"]
    if args:
        body = simplify_expression(ast["body"], ".ret")
        for i, arg in reversed(list(enumerate(args))):
            if i: name = ast["name"] + "." + str(i)
            else: name = ast["name"]
            body = {
                "type": "fn",
                "name": name,
                "arg": arg,
                "body": ast["body"]
            }
        ast["body"] = body
    else:
        ast["body"] = simplify_expression(ast["body"], ast["name"])

    del ast["args"]

    return ast

def simplify_name(ast, name):
    return ast

def simplify_call(ast, name):
    *calls, arg = ast["args"]

    if len(calls) > 1:
        call = ast.copy()
        call["args"] = calls
    else:
        call = calls[0]

    call = simplify_expression(call, name + ".call")
    arg = simplify_expression(arg, name + ".arg")

    ast["name"] = name
    ast["call"] = call
    ast["arg"] = arg
    del ast["args"]

    return ast

def simplify_block(ast, name):
    ast["name"] = name

    ast["body"] = [
        simplify_expression(e, name + "." + str(i) if i < len(ast["body"])-1 else name)
        for i, e in enumerate(ast["body"])
    ]

    return ast

def simplify_integer(ast, name):
    return ast

def simplify_instruction(ast, name):
    ast["name"] = name
    return ast

def simplify_expression(ast, name):
    if ast["type"] == "def":
        return simplify_def(ast, name)
    elif ast["type"] == "name":
        return simplify_name(ast, name)
    elif ast["type"] == "call":
        return simplify_call(ast, name)
    elif ast["type"] == "block":
        return simplify_block(ast, name)
    elif ast["type"] == "integer":
        return simplify_integer(ast, name)
    elif ast["type"] == "instruction":
        return simplify_instruction(ast, name)
    else:
        raise ValueError("Wrong ast type: " + str(ast["type"]))

def simplify_ast(ast):
    return simplify_expression(ast, ".ret")


if __name__ == "__main__":
    import json
    import sys

    ast = json.load(sys.stdin)
    simplified_ast = simplify_ast(ast)
    json.dump(simplified_ast, sys.stdout, indent=4)
    sys.stdout.write("\n")
