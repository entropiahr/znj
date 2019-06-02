#!/usr/bin/env python3

def parse_expression(tokens):
    passed = []

    while tokens:
        t, *tokens = tokens

        if t['type'] in ('name', 'integer'):
            passed.append(t)
        elif t['type'] == 'def':
            if not passed:
                raise ValueError("Lhs of a definition is empty.")
            for p in passed:
                if p['type'] != 'name':
                    raise ValueError(f"Found something that is not a name on lhs of a definition: {repr(p)}")
            name, *args = [p['name'] for p in passed]
            body, tokens = parse_expression(tokens)
            expression = {
                'type': 'def',
                'name': name,
                'args': args,
                'body': body,
            }
            return (expression, tokens)
        elif t['type'] == 'instruction':
            if passed:
                raise ValueError("Using keyword 'instruction' in a wrong place.")

            passed = [{'type': 'instruction'}]
        elif t['type'] == 'external':
            if passed:
                raise ValueError("Using keyword 'external' in a wrong place.")

            passed = [{'type': 'external'}]

        if t['type'] == 'term' or not tokens:
            if not passed:
                raise ValueError("Expression is empty.")

            if passed[0]['type'] == 'instruction':
                args = passed[1:]

                if not args or args[0]['type'] != 'name':
                    raise ValueError("Keyword 'instruction' must be followed by instruction name.")

                name = args[0]['name']
                args = args[1:]

                expression = {
                    'type': 'instruction',
                    'instruction': name,
                    'args': args,
                }
                return (expression, tokens)
            elif passed[0]['type'] == 'external':
                if len(passed) != 3 or passed[1]['type'] != 'name' or passed[2]['type'] != 'integer':
                    raise ValueError("Keyword 'external' must be followed by name and number of arguments.")

                name = passed[1]['name']

                vtype = ['Int']
                for _ in passed[2]['value']:
                    vtype = ['->', ['Int'], vtype]

                expression = {
                    'type': 'external',
                    'name': name,
                    'vtype': vtype,
                }
                return (expression, tokens)
            else:
                if len(passed) == 1:
                    return (passed[0], tokens)

                expression = {
                    'type': 'call',
                    'args': passed,
                }
                return (expression, tokens)


def parser(tokens):
    body = []
    while tokens:
        b, tokens = parse_expression(tokens)
        body.append(b)
    return {'type': 'block', 'body': body}


if __name__ == '__main__':
    import json
    import sys

    ast = json.load(sys.stdin)
    parsed_ast = parser(ast)
    json.dump(parsed_ast, sys.stdout, indent=2)
    sys.stdout.write('\n')
