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

    @pytest.mark.parametrize("given, expected", [
        (None, None),
    ])
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize("given", [
        123,
        "spam"
    ])
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_error(loc, "modelity.NoneRequired"),)


class TestIntParser:

    @pytest.fixture
    def tp(self):
        return int

    @pytest.mark.parametrize("given, expected", [
        (1, 1),
        ("2", 2),
    ])
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize("given", [
        "foo", "3.14", [], {}, set(), tuple(),
    ])
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_error(loc, "modelity.IntegerRequired"),)


class TestFloatParser:

    @pytest.fixture
    def tp(self):
        return float

    @pytest.mark.parametrize("given, expected", [
        (1, 1.0),
        ("2.1", 2.1),
    ])
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize("given", [
        "foo", [], {}, set(), tuple(),
    ])
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_error(loc, "modelity.FloatRequired"),)


class TestStrParser:

    @pytest.fixture
    def tp(self):
        return str

    @pytest.mark.parametrize("given, expected", [
        ("foo", "foo"),
    ])
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize("given", [
        123
    ])
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_error(loc, "modelity.StringRequired"),)


class TestBoolParser:

    @pytest.fixture
    def tp(self):
        return bool

    @pytest.mark.parametrize("given, expected", [
        (True, True),
        (1, True),
        ("on", True),
        ("true", True),
        (False, False),
        (0, False),
        ("off", False),
        ("false", False),
    ])
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize("given", [
        2,
        None,
        "dummy",
        [],
        {}
    ])
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_error(loc, "modelity.BooleanRequired"),)


class TestOptionalParser:

    @pytest.mark.parametrize("tp, given, expected", [
        (Optional[int], 1, 1),
        (Optional[int], "2", 2),
        (Optional[int], None, None),
    ])
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize("tp, given, supported_types", [
        (Optional[str], 123, (str, NoneType)),
    ])
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given, supported_types):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_unsupported_type_error(loc, supported_types),)


class TestUnionParser:

    @pytest.mark.parametrize("tp, given, expected", [
        (Union[int, str], 123, 123),
        (Union[int, str], "123", "123"),
    ])
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize("tp, given, supported_types", [
        (Union[str, int, float], None, (str, int, float)),
    ])
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given, supported_types):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (make_unsupported_type_error(loc, supported_types),)


@pytest.mark.skip
class TestSuccessfulParsing:

    @pytest.fixture(
        params=[
            (int, 1, 1),
            (int, 3.14, 3),
            (int, "4", 4),
            (str, "foo", "foo"),
            (str, "4", "4"),
            (tuple, (1, "foo", 3.14), (1, "foo", 3.14)),
            (tuple, [1, "foo", 3.14], (1, "foo", 3.14)),
            (Tuple[str], ("foo",), ("foo",)),
            (Tuple[int, ...], (1, 2), (1, 2)),
            (list, [1, "foo", 3.14], [1, "foo", 3.14]),
            (list, (1, "foo", 3.14), [1, "foo", 3.14]),
            (set, {1, "foo", 3.14}, {1, "foo", 3.14}),
            (set, [1, 2, 1, 2], {1, 2}),
            (dict, {1: "one"}, {1: "one"}),
            (dict, [(1, "one")], {1: "one"}),
            (type(None), None, None),
            (Optional[int], None, None),
            (Optional[int], 1, 1),
            (Optional[int], "2", 2),
            (Optional[str], None, None),
            (Optional[str], "foo", "foo"),
            (Union[int, str, NoneType], 0, 0),
            (Union[int, str, NoneType], "123", 123),
            (Union[int, str, NoneType], "foo", "foo"),
            (Union[int, str, NoneType], None, None),
        ]
    )
    def data(self, request: pytest.FixtureRequest):
        return request.param

    @pytest.fixture
    def tp(self, data: tuple):
        return data[0]

    @pytest.fixture
    def loc(self):
        return tuple()

    @pytest.fixture
    def given(self, data: tuple):
        return data[1]

    @pytest.fixture
    def expected(self, data: tuple):
        return data[2]

    def test_parse_value_successfully_and_return_expected_result(
        self, parser: IParser, loc: tuple, given: Any, expected: Any
    ):
        assert parser(loc, given) == expected


@pytest.mark.skip
class TestParsingErrors:

    @pytest.fixture(
        params=[
            (int, None, [(tuple(), "modelity.parsing.INT_REQUIRED", {"given": None})]),
            (int, "foo", [(tuple(), "modelity.parsing.INT_REQUIRED", {"given": "foo"})]),
            (str, 123, [(tuple(), "String value required")]),
            (tuple, 123, [(tuple(), "Not a valid tuple")]),
            # (Tuple[str, ...], (123,), [(tuple(), "Tuple of <class 'str'> elements required")]),
            (list, 123, [(tuple(), "Not a valid list")]),
            (set, 123, [(tuple(), "Not a valid set")]),
            (dict, 123, [(tuple(), "Not a valid dict")]),
            (type(None), 123, [(tuple(), "None value required")]),
            (
                Optional[str],
                123,
                [(tuple(), "Unsupported type of input value; supported ones are: <class 'str'>, <class 'NoneType'>")],
            ),
            (
                Optional[int],
                "foo",
                [(tuple(), "Unsupported type of input value; supported ones are: <class 'int'>, <class 'NoneType'>")],
            ),
        ]
    )
    def data(self, request: pytest.FixtureRequest):
        return request.param

    @pytest.fixture
    def tp(self, data: tuple):
        return data[0]

    @pytest.fixture
    def loc(self):
        return tuple()

    @pytest.fixture
    def given(self, data: tuple):
        return data[1]

    @pytest.fixture
    def expected_errors(self, data: tuple):
        return data[2]

    def test_parsing_fails_if_input_value_cannot_be_parsed(
        self, parser: IParser, loc: tuple, given: Any, expected_errors: str
    ):
        with pytest.raises(ParsingError) as excinfo:
            parser(loc, given)
        assert excinfo.value.errors == [ParsingError.ErrorItem(*x) for x in expected_errors]
