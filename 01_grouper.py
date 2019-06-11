#!/usr/bin/env python3

"""
This module groups all blocks and operators.

Rules:
literal|name|keyword|call|block|operator -> ex
ex ex -> call
()|(ex, ex, ...)|(ex; ex; ...) -> block
ex op ex -> operator

AST:
{"type": "integer", "value": number}
{"type": "name", "value": string}
{"type": "instruction", "instruction": string, "args": [ex]}
{"type": "external", "external": string}
{"type": "block", "seperator": string|null, "expressions": [ex]}
{"type": "operator", "operator": string, "lhs": ex, "rhs": ex}

Guarantees:
"operator" "lhs" and "rhs" are non-empty.
"expression" "items" are non-empty.
Root will allways be a "block" with seperator ";".
"""

GROUP_TERMINATORS = [')', 'EOF']
SEPERATORS = [';', ',']
EXPRESSION_TERMINATORS = GROUP_TERMINATORS + SEPERATORS
OPERATORS = {
    'call': 0,
    '->': 1,
    '=': 1,
}


def unexpected_token_error(token):
    return ValueError(f"Unexpected token at this position: {token}")


def parse_operators(items, lhs, op, rhs):
    if items:
        new_op, new_rhs, *new_items = items

        if op:
            if OPERATORS[op] < OPERATORS[new_op]:
                lhs = parse_operators([], lhs, op, rhs)
                return parse_operators(new_items, lhs, new_op, new_rhs)
            else:
                rhs = parse_operators(new_items, rhs, new_op, new_rhs)
                return parse_operators([], lhs, op, rhs)
        else:
            return parse_operators(new_items, lhs, new_op, new_rhs)
    else:
        return {
            'type': 'operator',
            'operator': op,
            'lhs': lhs,
            'rhs': rhs,
        }


def parse_external(external, items):
    if not items and items[0]['type'] == 'name':
        raise ValueError(f"External must be followed by external name: {external}")

    name, *new_items = items
    external = {'type': 'external', 'external': name['value']}
    return external, new_items


def parse_instruction(instruction, items):
    if len(items) < 2 and items[0]['type'] == 'name':
        raise ValueError(f"Instruction must be followed by instruction name and instruction arguments: {instruction}")

    name, args, *new_items = items

    if args['type'] == 'block' and args['seperator'] == ',':
        instruction = {'type': 'instruction', 'instruction': name['value'], 'args': args['expressions']}
        return instruction, new_items
    else:
        raise ValueError(f"Instruction arguments must be tuple: {args}")


def check_expression(items):
    if items:
        item, *items = items

        if item['type'] in OPERATORS:
            raise ValueError(f"Operator is missing LHS: {item}")
        elif item['type'] == 'instruction':
            item, items = parse_instruction(item, items)
        elif item['type'] == 'external':
            item, items = parse_external(item, items)

        if items:
            op, *new_items = items

            if op['type'] in OPERATORS:
                return [item, op['type']] + check_expression(new_items)
            else:
                return [item, 'call'] + check_expression(items)
        else:
            return [item]
    else:
        raise ValueError("Operator is missing RHS.")


def group_expression(tokens, items):
    token, *new_tokens = tokens

    if token['type'] in EXPRESSION_TERMINATORS:
        if items:
            lhs, *items = check_expression(items)
            if items:
                op, rhs, *items = items
                expression = parse_operators(items, lhs, op, rhs)
            else:
                expression = lhs
            return (expression, tokens)
        else:
            raise unexpected_token_error(token)
    elif token['type'] == '(':
        item, new_tokens = group_block(new_tokens, [], ')', None)
        return group_expression(new_tokens, items + [item])
    else:
        return group_expression(new_tokens, items + [token])


def group_block(tokens, expressions, end_type, seperator):
    token, *new_tokens = tokens

    if token['type'] in GROUP_TERMINATORS:
        if token['type'] == end_type and not expressions:
            return ({'type': 'block', 'seperator': seperator, 'expressions': []}, new_tokens)
        else:
            raise unexpected_token_error(token)
    else:
        (expression, new_tokens) = group_expression(tokens, [])
        expressions.append(expression)

    token, *new_tokens = new_tokens

    if token['type'] in SEPERATORS:
        if seperator:
            if token['type'] != seperator:
                raise unexpected_token_error(token)
        else:
            seperator = token['type']

        return group_block(new_tokens, expressions, end_type, seperator)
    elif token['type'] in GROUP_TERMINATORS:
        if token['type'] == end_type:
            return ({'type': 'block', 'seperator': seperator, 'expressions': expressions}, new_tokens)
        else:
            raise unexpected_token_error(token)
    else:
        raise unexpected_token_error(token)


def grouper(tokens):
    root, tokens = group_block(tokens, [], 'EOF', ';')

    if tokens:
        raise ValueError(f"Parser could not read all tokens:\n{tokens}")

    return root


if __name__ == '__main__':
    import json
    import sys

    ast = json.load(sys.stdin)
    ast = grouper(ast)
    json.dump(ast, sys.stdout, indent=2)
    sys.stdout.write('\n')
