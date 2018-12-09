from string import ascii_letters
from hypothesis import given
import hypothesis.strategies as st
import pytest

from lexer.lexer import DefaultMatcher, Token, matchers
from lexer.lexer import WhitespaceMatcher, NewlinesMatcher, SymbolMatcher, SpecialMatcher, StringMatcher, NumberMatcher


def test_empty():
    for matcher in matchers:
        assert None is matcher.get_regex().match("")


class TestDefaultMatcher:
    @staticmethod
    def test_abstract_calls_raise():
        pytest.raises(NotImplementedError, DefaultMatcher.get_regex)
        pytest.raises(NotImplementedError, DefaultMatcher.get_kind)
        pytest.raises(NotImplementedError, DefaultMatcher.create_token, "?", 1, (1, 1))
        pytest.raises(NotImplementedError, DefaultMatcher.get_match, "?")

    @staticmethod
    def test_update_dpos_succeeds():
        token = Token(pos=13, dpos=(5, 6), kind="?", val="myval", len=5)
        assert DefaultMatcher.update_dpos(token) == (5, 11)


class TestWhitespaceMatcher:
    matcher = WhitespaceMatcher

    @given(st.lists(st.one_of(map(st.just, [" ", "\t", "\f", "\v"])), min_size=1))
    def test_regex_with_valid_choices(self, values):
        text = ''.join(values)
        assert self.matcher.get_match(text).span() == (0, len(values))

    def test_regex_with_newline_fails(self):
        assert None is self.matcher.get_match("\n ")


class TestNewlinesMatcher:
    matcher = NewlinesMatcher

    @given(st.lists(st.just("\n"), min_size=1))
    def test_regex_with_newlines(self, values):
        text = ''.join(values)
        assert self.matcher.get_match(text).span() == (0, len(values))

    def test_update_dpos(self):
        token = Token(pos=13, dpos=(5, 6), kind="?", val="\n" * 5, len=5)
        assert self.matcher.update_dpos(token) == (10, 1)


class TestSymbolMatcher:
    matcher = SymbolMatcher

    @given(st.text(alphabet=ascii_letters, min_size=1))
    def test_regex_succeeds(self, text):
        assert self.matcher.get_match(text).span() == (0, len(text))


class TestSpecialMatcher:
    regex = SpecialMatcher.get_regex()

    @given(st.one_of(map(st.just, ["-", "+", "=", "(", ")", ";"])))
    def test_regex_and_kind_succeed(self, letter):
        assert self.regex.match(letter).span() == (0, 1)
        assert SpecialMatcher.get_kind(letter) == "special:{}".format(letter)


class TestStringMatcher:
    regex = StringMatcher.get_regex()

    @given(st.characters(blacklist_characters="\""))
    def test_regex_succeeds(self, chars):
        text = "\"" + chars + "\""
        assert self.regex.match(text).span() == (0, len(text))


class TestNumberMatcher:
    regex = NumberMatcher.get_regex()

    @given(st.one_of(st.integers(), st.floats(allow_infinity=False, allow_nan=False)))
    def test_regex_succeeds(self, number):
        text = str(number)
        assert self.regex.match(text).span() == (0, len(text))
