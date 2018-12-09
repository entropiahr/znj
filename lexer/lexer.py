import re
from collections import namedtuple
from pprint import pprint

Token = namedtuple('Token', 'pos dpos kind val')


class DefaultMatcher:
    """Abstract class, should not use directly"""

    regex = None
    kind = None

    @classmethod
    def get_regex(cls):
        if cls.regex:
            return cls.regex
        raise NotImplementedError()

    @classmethod
    def get_kind(cls, _value=None):
        if cls.kind:
            return cls.kind
        raise NotImplementedError()

    @classmethod
    def create_token(cls, value, pos, dpos):
        kind = cls.get_kind(value)
        return Token(pos=pos, dpos=dpos, kind=kind, val=value)

    @classmethod
    def update_dpos(cls, token):
        return token.dpos[0], token.dpos[1] + len(token.val)

    @classmethod
    def get_match(cls, text):
        return cls.get_regex().match(text)


class WhitespaceMatcher(DefaultMatcher):
    regex = re.compile(r'^[ \t\f\v]+')
    kind = "whitespace"


class NewlinesMatcher(DefaultMatcher):
    regex = re.compile(r'^\n+')
    kind = "newlines"

    @classmethod
    def update_dpos(cls, token):
        return token.dpos[0] + len(token.val), 1


class SymbolMatcher(DefaultMatcher):
    regex = re.compile(r'^[_a-zA-Z]+[!?]?')
    kind = "symbol"


class SpecialMatcher(DefaultMatcher):
    regex = re.compile(r'^[-+=\(\)\;]')

    @classmethod
    def get_kind(cls, value=None):
        if not value:
            raise AttributeError("Value must be provided")
        return "special:" + value


class StringMatcher(DefaultMatcher):
    regex = re.compile(r'^"[^"]*"')
    kind = "string"


class NumberMatcher(DefaultMatcher):
    regex = re.compile(r'[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?')
    kind = "number"


matchers = [WhitespaceMatcher, NewlinesMatcher, SymbolMatcher, SpecialMatcher, StringMatcher, NumberMatcher]


def run():
    with open('example.znj', 'r') as f:
        code = f.read()
        position, length = 0, len(code)
        dpos = 1, 1
        tokens = []
        while position < length:
            matcher, match = find_matcher(code, position)
            if match:
                token_len = match.span()[1]
                value = code[position:position + token_len]
                token = matcher.create_token(value, position, dpos)
                position += token_len
                dpos = matcher.update_dpos(token)
                tokens.append(token)
                continue
            break
        pprint(tokens)
        if position == length:
            print("EOF reached!")
        exit(0)


def find_matcher(code, position):
    for matcher in matchers:
        match = matcher.get_match(code[position:])
        if match:
            return matcher, match
    return None, None


if __name__ == "__main__":
    run()
