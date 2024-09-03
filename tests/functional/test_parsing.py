from types import NoneType
from typing import Any, List, Optional, Tuple, Type, Union

import pytest

from modelity.error import Error
from modelity.exc import ParsingError
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


class TestListParser:

    @pytest.mark.parametrize(
        "tp, given, expected",
        [
            (list, [], []),
            (list, "123", ["1", "2", "3"]),
            (List[Any], [1, 2, "foo"], [1, 2, "foo"]),
            (List[int], [1, 2, "3"], [1, 2, 3]),
            (List[Union[int, str]], [1, 2, "foo"], [1, 2, "foo"]),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize(
        "tp, given, expected_errors",
        [
            (list, None, (make_error(tuple(), "modelity.IterableRequired"),)),
            (list[int], None, (make_error(tuple(), "modelity.IterableRequired"),)),
            (
                List[int],
                ["spam", 123, "dummy"],
                (
                    make_error((0,), "modelity.IntegerRequired"),
                    make_error((2,), "modelity.IntegerRequired"),
                ),
            ),
        ],
    )
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given, expected_errors):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == expected_errors

    class TestInterface:

        @pytest.fixture
        def tp(self):
            return List[int]

        @pytest.fixture
        def sut(self, parser: IParser, initial_value, loc):
            return parser(initial_value, loc)

        @pytest.mark.parametrize("initial_value, given_list", [
            ([], []),
            ([1, 2], [1, 2]),
            (["1", 2, 3], [1, 2, 3]),
        ])
        def test_check_equality_of_two_lists(self, sut: list, given_list):
            assert sut == given_list

        @pytest.mark.parametrize("initial_value, expected_repr", [
            ([], "[]"),
            ([1, 2], "[1, 2]"),
            (["1"], "[1]"),
        ])
        def test_repr(self, sut: list, expected_repr):
            assert repr(sut) == expected_repr

        @pytest.mark.parametrize("initial_value, index, expected_result", [
            ([1], 0, []),
        ])
        def test_delitem(self, sut: list, index, expected_result):
            del sut[index]
            assert sut == expected_result

        @pytest.mark.parametrize("initial_value, index", [
            ([], 0),
            ([1, 2], 2),
        ])
        def test_delitem_throws_index_error_if_index_is_invalid(self, sut: list, index):
            with pytest.raises(IndexError) as excinfo:
                del sut[index]
            assert str(excinfo.value) == "list assignment index out of range"

        @pytest.mark.parametrize("initial_value, index, expected_result", [
            ([1], 0, 1),
            ([1, "2"], 1, 2),
        ])
        def test_getitem(self, sut: list, index, expected_result):
            assert sut[index] == expected_result

        @pytest.mark.parametrize("initial_value, index", [
            ([], 0),
            ([1, 2], 2),
        ])
        def test_getitem_throws_index_error_if_index_is_invalid(self, sut: list, index):
            with pytest.raises(IndexError) as excinfo:
                _ = sut[index]
            assert str(excinfo.value) == "list index out of range"

        @pytest.mark.parametrize("initial_value, index, value, expected_result", [
            ([1], 0, 2, [2]),
            ([1, 2], 0, "3", [3, 2]),
            ([1, 2, 3], 2, "4", [1, 2, 4]),
        ])
        def test_setitem(self, sut: list, index, value, expected_result):
            sut[index] = value
            assert sut == expected_result

        @pytest.mark.parametrize("initial_value, index, value, expected_result", [
            ([1], 0, "spam", [1]),
        ])
        def test_setitem_fails_if_invalid_input_given(self, sut: list, index, value, expected_result):
            with pytest.raises(ParsingError) as excinfo:
                sut[index] = value
            assert sut == expected_result
            assert excinfo.value.errors == (Error.create(tuple(), "modelity.IntegerRequired"),)

        @pytest.mark.parametrize("initial_value, expected_length", [
            ([], 0),
            ([1, 2, 3], 3),
        ])
        def test_length(self, sut: list, expected_length):
            assert len(sut) == expected_length

        @pytest.mark.parametrize("initial_value, index, value, expected_result", [
            ([], 0, "1", [1]),
            ([2], 0, "1", [1, 2]),
            ([1, 2], 1, "3", [1, 3, 2]),
        ])
        def test_insert_element_to_the_list(self, sut: list, index, value, expected_result):
            sut.insert(index, value)
            assert sut == expected_result

        @pytest.mark.parametrize("initial_value, index, value, expected_result", [
            ([1], 0, "spam", [1]),
        ])
        def test_insert_fails_if_invalid_input_given(self, sut: list, index, value, expected_result):
            with pytest.raises(ParsingError) as excinfo:
                sut.insert(index, value)
            assert sut == expected_result
            assert excinfo.value.errors == (Error.create(tuple(), "modelity.IntegerRequired"),)
