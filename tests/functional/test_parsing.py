from types import NoneType
from typing import Any, Optional, Tuple, Type, Union

import pytest

from modelity.error import Error
from modelity.invalid import Invalid
from modelity.parsing.parsers import all
from modelity.parsing.interface import IParser, IParserRegistry


def make_error(loc: tuple, code: str, **data: Any) -> Error:
    return Error(loc, code, data)


def make_unsupported_type_error(loc: tuple, supported_types: tuple[type]) -> Error:
    return make_error(loc, "modelity.UnsupportedType", supported_types=supported_types)


@pytest.fixture
def registry():
    return all.registry


@pytest.fixture
def parser(registry: IParserRegistry, tp: Type):
    return registry.require_parser(tp)


@pytest.fixture
def loc():
    return tuple()


class TestNoneParser:

    @pytest.fixture
    def tp(self):
        return NoneType

    @pytest.mark.parametrize(
        "given, expected",
        [
            (None, None),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize("given", [123, "spam"])
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_error(loc, "modelity.NoneRequired"),)


class TestIntParser:

    @pytest.fixture
    def tp(self):
        return int

    @pytest.mark.parametrize(
        "given, expected",
        [
            (1, 1),
            ("2", 2),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize(
        "given",
        [
            "foo",
            "3.14",
            [],
            {},
            set(),
            tuple(),
        ],
    )
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_error(loc, "modelity.IntegerRequired"),)


class TestFloatParser:

    @pytest.fixture
    def tp(self):
        return float

    @pytest.mark.parametrize(
        "given, expected",
        [
            (1, 1.0),
            ("2.1", 2.1),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize(
        "given",
        [
            "foo",
            [],
            {},
            set(),
            tuple(),
        ],
    )
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_error(loc, "modelity.FloatRequired"),)


class TestStrParser:

    @pytest.fixture
    def tp(self):
        return str

    @pytest.mark.parametrize(
        "given, expected",
        [
            ("foo", "foo"),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize("given", [123])
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_error(loc, "modelity.StringRequired"),)


class TestBoolParser:

    @pytest.fixture
    def tp(self):
        return bool

    @pytest.mark.parametrize(
        "given, expected",
        [
            (True, True),
            (1, True),
            ("on", True),
            ("true", True),
            (False, False),
            (0, False),
            ("off", False),
            ("false", False),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize("given", [2, None, "dummy", [], {}])
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_error(loc, "modelity.BooleanRequired"),)


class TestOptionalParser:

    @pytest.mark.parametrize(
        "tp, given, expected",
        [
            (Optional[int], 1, 1),
            (Optional[int], "2", 2),
            (Optional[int], None, None),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize(
        "tp, given, supported_types",
        [
            (Optional[str], 123, (str, NoneType)),
        ],
    )
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given, supported_types):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_unsupported_type_error(loc, supported_types),)


class TestUnionParser:

    @pytest.mark.parametrize(
        "tp, given, expected",
        [
            (Union[int, str], 123, 123),
            (Union[int, str], "123", "123"),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize(
        "tp, given, supported_types",
        [
            (Union[str, int, float], None, (str, int, float)),
        ],
    )
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given, supported_types):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_unsupported_type_error(loc, supported_types),)


class TestTupleParser:

    @pytest.mark.parametrize(
        "tp, given, expected",
        [
            (tuple, [], tuple()),
            (tuple, "123", ("1", "2", "3")),
            (Tuple[Any, ...], [1, 2, 3], (1, 2, 3)),
            (Tuple[int, ...], ["1", "2"], (1, 2)),
            (Tuple[int, str], ["1", "foo"], (1, "foo")),
            (Tuple[int, str, float], ["1", "foo", "3.14159"], (1, "foo", 3.14159)),
            (Tuple[tuple, ...], [(1,)], ((1,),)),
            (Tuple[Tuple[int]], [("1",)], ((1,),)),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize(
        "tp, given, expected_errors",
        [
            (tuple, None, (make_error(tuple(), "modelity.IterableRequired"),)),
            (Tuple[int, ...], None, (make_error(tuple(), "modelity.IterableRequired"),)),
            (Tuple[int, str, float], None, (make_error(tuple(), "modelity.IterableRequired"),)),
            (
                Tuple[int, str, float],
                ["1"],
                (make_error(tuple(), "modelity.InvalidTupleFormat", expected_format=(int, str, float)),),
            ),
            (
                Tuple[int, str, float],
                ["foo"],
                (make_error(tuple(), "modelity.InvalidTupleFormat", expected_format=(int, str, float)),),
            ),
            (
                Tuple[int, str, float],
                [123, "foo", "bar"],
                (make_error((2,), "modelity.FloatRequired"),),
            ),
            (
                Tuple[int, str, float],
                ["spam", "foo", "3.14"],
                (make_error((0,), "modelity.IntegerRequired"),),
            ),
            (
                Tuple[int, str, float],
                ["spam", 123, "dummy"],
                (
                    make_error((0,), "modelity.IntegerRequired"),
                    make_error((1,), "modelity.StringRequired"),
                    make_error((2,), "modelity.FloatRequired"),
                ),
            ),
            (Tuple[int, ...], [1, 2, 3, "spam"], (make_error((3,), "modelity.IntegerRequired"),)),
            (Tuple[Tuple[int]], [1], (make_error((0,), "modelity.IterableRequired"),)),
            (Tuple[Tuple[int, ...]], [["1", 2, "3", "spam", 4]], (make_error((0, 3), "modelity.IntegerRequired"),)),
        ],
    )
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given, expected_errors):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == expected_errors
