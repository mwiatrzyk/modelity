import enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Set, Tuple, Type, Union

import pytest

from modelity.error import Error
from modelity.exc import ParsingError
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.model import Model
from modelity.parsing.type_parsers import all
from modelity.interface import IParser, ITypeParserProvider
from modelity.validators import Max, Min, Range
from tests.helpers import ErrorFactoryHelper


def make_error(loc: Loc, code: str, **data: Any) -> Error:
    return Error(loc, code, data)


def make_unsupported_type_error(loc: Loc, supported_types: tuple[type]) -> Error:
    return make_error(loc, "modelity.UnsupportedType", supported_types=supported_types)


@pytest.fixture
def registry():
    return all.provider


@pytest.fixture
def parser(registry: ITypeParserProvider, tp: Type):
    return registry.provide_type_parser(tp)


@pytest.fixture
def loc():
    return Loc()


class TestNoneParser:

    @pytest.fixture
    def tp(self):
        return type(None)

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
        assert result.errors == tuple([ErrorFactoryHelper.none_required(loc)])


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
        assert result.errors == tuple([ErrorFactoryHelper.integer_required(loc)])


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
        assert result.errors == tuple([ErrorFactoryHelper.float_required(loc)])


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
        assert result.errors == tuple([ErrorFactoryHelper.string_required(loc)])


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
        assert result.errors == tuple([ErrorFactoryHelper.boolean_required(loc)])


class TestEnumParser:

    class Dummy(enum.Enum):
        FOO = 1
        BAR = 2
        BAZ = 3

    @pytest.fixture
    def tp(self):
        return self.Dummy

    @pytest.mark.parametrize(
        "given, expected",
        [
            (1, Dummy.FOO),
            (2, Dummy.BAR),
            (3, Dummy.BAZ),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize(
        "given",
        [
            0,
        ],
    )
    def test_parsing_fails_if_input_value_does_not_match_any_enum(self, parser: IParser, given, loc):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == tuple(
            [
                ErrorFactoryHelper.invalid_enum(
                    loc,
                    supported_values=(self.Dummy.FOO, self.Dummy.BAR, self.Dummy.BAZ),
                )
            ]
        )


class TestLiteralParser:

    @pytest.mark.parametrize(
        "tp, given",
        [
            (Literal["foo"], "foo"),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given):
        assert parser(given, loc) == given

    @pytest.mark.parametrize(
        "tp, given, supported_values",
        [
            (Literal["foo"], "bar", ["foo"]),
        ],
    )
    def test_parsing_fails_if_input_value_is_out_of_literal_range(self, parser: IParser, given, supported_values):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == tuple(
            [ErrorFactoryHelper.invalid_literal(loc, supported_values=tuple(supported_values))]
        )


class TestAnnotated:

    @pytest.mark.parametrize(
        "tp, given, expected",
        [
            (Annotated[int, Range(1, 10)], 1, 1),
            (Annotated[int, Range(1, 10)], "10", 10),
            (Annotated[float, Range(0, 1)], "0", 0.0),
            (Annotated[float, Range(0, 1)], "1", 1.0),
        ],
    )
    def test_successfully_parse_annotated_type(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize(
        "tp, given, invalid_value, expected_error",
        [
            (
                Annotated[int, Range(1, 10)],
                "spam",
                "spam",
                ErrorFactoryHelper.integer_required(Loc()),
            ),
            (
                Annotated[int, Range(1, 10)],
                "0",
                0,
                ErrorFactoryHelper.value_out_of_range(Loc(), min=1, max=10),
            ),
            (
                Annotated[int, Range(1, 10)],
                "11",
                11,
                ErrorFactoryHelper.value_out_of_range(Loc(), min=1, max=10),
            ),
            (
                Annotated[int, Min(1), Max(2)],
                0,
                0,
                ErrorFactoryHelper.value_too_low(Loc(), min=1),
            ),
            (
                Annotated[int, Min(1), Max(2)],
                3,
                3,
                ErrorFactoryHelper.value_too_high(Loc(), max=2),
            ),
        ],
    )
    def test_parsing_fails_if_input_value_is_invalid(self, parser: IParser, given, invalid_value, loc, expected_error):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == invalid_value
        assert result.errors == tuple([expected_error])


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
            (Optional[str], 123, (str, type(None))),
        ],
    )
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given, supported_types):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == (ErrorFactoryHelper.unsupported_type(loc, supported_types),)


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
        assert result.errors == (ErrorFactoryHelper.unsupported_type(loc, supported_types),)


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
            (tuple, None, (ErrorFactoryHelper.iterable_required(Loc()),)),
            (Tuple[int, ...], None, (ErrorFactoryHelper.iterable_required(Loc()),)),
            (Tuple[int, str, float], None, (ErrorFactoryHelper.iterable_required(Loc()),)),
            (
                Tuple[int, str, float],
                ["1"],
                (ErrorFactoryHelper.invalid_tuple_format(Loc(), expected_format=(int, str, float)),),
            ),
            (
                Tuple[int, str, float],
                ["foo"],
                (ErrorFactoryHelper.invalid_tuple_format(Loc(), expected_format=(int, str, float)),),
            ),
            (
                Tuple[int, str, float],
                [123, "foo", "bar"],
                (ErrorFactoryHelper.float_required(Loc(2)),),
            ),
            (
                Tuple[int, str, float],
                ["spam", "foo", "3.14"],
                (ErrorFactoryHelper.integer_required(Loc(0)),),
            ),
            (
                Tuple[int, str, float],
                ["spam", 123, "dummy"],
                (
                    ErrorFactoryHelper.integer_required(Loc(0)),
                    ErrorFactoryHelper.string_required(Loc(1)),
                    ErrorFactoryHelper.float_required(Loc(2)),
                ),
            ),
            (Tuple[int, ...], [1, 2, 3, "spam"], (ErrorFactoryHelper.integer_required(Loc(3)),)),
            (Tuple[Tuple[int]], [1], (ErrorFactoryHelper.iterable_required(Loc(0)),)),
            (
                Tuple[Tuple[int, ...]],
                [["1", 2, "3", "spam", 4]],
                (ErrorFactoryHelper.integer_required(Loc(0, 3)),),
            ),
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
            (list, None, (ErrorFactoryHelper.iterable_required(Loc()),)),
            (list[int], None, (ErrorFactoryHelper.iterable_required(Loc()),)),
            (
                List[int],
                ["spam", 123, "dummy"],
                (
                    ErrorFactoryHelper.integer_required(Loc(0)),
                    ErrorFactoryHelper.integer_required(Loc(2)),
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

        @pytest.mark.parametrize(
            "initial_value, given_list",
            [
                ([], []),
                ([1, 2], [1, 2]),
                (["1", 2, 3], [1, 2, 3]),
            ],
        )
        def test_check_equality_of_two_lists(self, sut: list, given_list):
            assert sut == given_list

        @pytest.mark.parametrize(
            "initial_value, expected_repr",
            [
                ([], "[]"),
                ([1, 2], "[1, 2]"),
                (["1"], "[1]"),
            ],
        )
        def test_repr(self, sut: list, expected_repr):
            assert repr(sut) == expected_repr

        @pytest.mark.parametrize(
            "initial_value, index, expected_result",
            [
                ([1], 0, []),
            ],
        )
        def test_delitem(self, sut: list, index, expected_result):
            del sut[index]
            assert sut == expected_result

        @pytest.mark.parametrize(
            "initial_value, index",
            [
                ([], 0),
                ([1, 2], 2),
            ],
        )
        def test_delitem_throws_index_error_if_index_is_invalid(self, sut: list, index):
            with pytest.raises(IndexError) as excinfo:
                del sut[index]
            assert str(excinfo.value) == "list assignment index out of range"

        @pytest.mark.parametrize(
            "initial_value, index, expected_result",
            [
                ([1], 0, 1),
                ([1, "2"], 1, 2),
            ],
        )
        def test_getitem(self, sut: list, index, expected_result):
            assert sut[index] == expected_result

        @pytest.mark.parametrize(
            "initial_value, index",
            [
                ([], 0),
                ([1, 2], 2),
            ],
        )
        def test_getitem_throws_index_error_if_index_is_invalid(self, sut: list, index):
            with pytest.raises(IndexError) as excinfo:
                _ = sut[index]
            assert str(excinfo.value) == "list index out of range"

        @pytest.mark.parametrize(
            "initial_value, index, value, expected_result",
            [
                ([1], 0, 2, [2]),
                ([1, 2], 0, "3", [3, 2]),
                ([1, 2, 3], 2, "4", [1, 2, 4]),
            ],
        )
        def test_setitem(self, sut: list, index, value, expected_result):
            sut[index] = value
            assert sut == expected_result

        @pytest.mark.parametrize(
            "initial_value, index, value, expected_result",
            [
                ([1], 0, "spam", [1]),
            ],
        )
        def test_setitem_fails_if_invalid_input_given(self, sut: list, index, value, expected_result):
            with pytest.raises(ParsingError) as excinfo:
                sut[index] = value
            assert sut == expected_result
            assert excinfo.value.errors == (ErrorFactoryHelper.integer_required(Loc()),)

        @pytest.mark.parametrize(
            "initial_value, expected_length",
            [
                ([], 0),
                ([1, 2, 3], 3),
            ],
        )
        def test_length(self, sut: list, expected_length):
            assert len(sut) == expected_length

        @pytest.mark.parametrize(
            "initial_value, index, value, expected_result",
            [
                ([], 0, "1", [1]),
                ([2], 0, "1", [1, 2]),
                ([1, 2], 1, "3", [1, 3, 2]),
            ],
        )
        def test_insert_element_to_the_list(self, sut: list, index, value, expected_result):
            sut.insert(index, value)
            assert sut == expected_result

        @pytest.mark.parametrize(
            "initial_value, index, value, expected_result",
            [
                ([1], 0, "spam", [1]),
            ],
        )
        def test_insert_fails_if_invalid_input_given(self, sut: list, index, value, expected_result):
            with pytest.raises(ParsingError) as excinfo:
                sut.insert(index, value)
            assert sut == expected_result
            assert excinfo.value.errors == (ErrorFactoryHelper.integer_required(Loc()),)


class TestDictParser:

    @pytest.mark.parametrize(
        "tp, given, expected",
        [
            (dict, [], {}),
            (dict, [("one", 1)], {"one": 1}),
            (Dict[str, int], [("one", 1)], {"one": 1}),
            (Dict[str, int], [("one", "1")], {"one": 1}),
            (Dict[int, str], {"1": "one"}, {1: "one"}),
            (Dict[str, Union[int, float]], {"foo": 1, "bar": "3.14"}, {"foo": 1, "bar": 3.14}),
            (Dict[str, List[int]], {"foo": [1, "2", "3"]}, {"foo": [1, 2, 3]}),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize(
        "tp, given, expected_errors",
        [
            (dict, None, (ErrorFactoryHelper.mapping_required(Loc()),)),
            (dict, [1, 2, 3], (ErrorFactoryHelper.mapping_required(Loc()),)),
            (
                Dict[str, int],
                [("one", "spam")],
                (ErrorFactoryHelper.integer_required(Loc("one")),),
            ),
            (Dict[int, str], [("one", "spam")], (ErrorFactoryHelper.integer_required(Loc()),)),
            (Dict[int, str], None, (ErrorFactoryHelper.mapping_required(Loc()),)),
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
            return Dict[str, int]

        @pytest.fixture
        def sut(self, parser: IParser, initial, loc):
            return parser(initial, loc)

        @pytest.mark.parametrize(
            "initial, expected_repr",
            [
                ({}, "{}"),
            ],
        )
        def test_repr(self, sut: list, expected_repr):
            assert repr(sut) == expected_repr

        @pytest.mark.parametrize(
            "initial, other",
            [
                ({}, {}),
                ({"one": 1}, {"one": 1}),
                ({"one": "1"}, {"one": 1}),
            ],
        )
        def test_check_equality_of_two_dicts(self, sut: dict, other):
            assert sut == other

        @pytest.mark.parametrize(
            "initial, key, value, expected_result",
            [
                ({}, "one", "2", {"one": 2}),
            ],
        )
        def test_set_item_to_given_value(self, sut: dict, key, value, expected_result):
            sut[key] = value
            assert sut == expected_result

        @pytest.mark.parametrize(
            "initial, key, value, expected_errors",
            [
                ({}, "one", "spam", [ErrorFactoryHelper.integer_required(Loc())]),
                ({}, 1, 2, [ErrorFactoryHelper.string_required(Loc())]),
            ],
        )
        def test_setting_item_to_invalid_value_causes_parsing_error(
            self, sut: dict, initial, key, value, expected_errors
        ):
            with pytest.raises(ParsingError) as excinfo:
                sut[key] = value
            assert sut == initial
            assert excinfo.value.errors == tuple(expected_errors)

        @pytest.mark.parametrize("initial, key, expected", [({"one": 1}, "one", {})])
        def test_delete_item(self, sut: dict, key, expected):
            del sut[key]
            assert sut == expected

        @pytest.mark.parametrize("initial, key", [({"one": 1}, "two")])
        def test_deleting_a_non_existing_key_causes_key_error(self, sut: dict, key):
            with pytest.raises(KeyError) as excinfo:
                del sut[key]
            assert excinfo.value.args[0] == key

        @pytest.mark.parametrize("initial, key, expected_value", [({"one": "1"}, "one", 1)])
        def test_get_item(self, sut: dict, key, expected_value):
            assert sut[key] == expected_value

        @pytest.mark.parametrize("initial, key", [({"one": 1}, "two")])
        def test_getting_a_non_existing_key_causes_key_error(self, sut: dict, key):
            with pytest.raises(KeyError) as excinfo:
                _ = sut[key]
            assert excinfo.value.args[0] == key

        @pytest.mark.parametrize("initial, expected_keys", [({"one": 1, "two": 2}, ["one", "two"])])
        def test_iterator_yields_dict_keys(self, sut: dict, expected_keys):
            assert list(iter(sut)) == expected_keys

        @pytest.mark.parametrize(
            "initial, expected_len",
            [
                ({}, 0),
                ({"one": 1}, 1),
                ({"one": 1, "two": 2}, 2),
            ],
        )
        def test_len_returns_number_of_items(self, sut: dict, expected_len):
            assert len(sut) == expected_len


class TestSetParser:

    @pytest.mark.parametrize(
        "tp, given, expected",
        [
            (set, [], set()),
            (set, [1], {1}),
            (set, [1, 1, "foo", "bar"], {1, "foo", "bar"}),
            (Set[int], [], set()),
            (Set[int], ["1", "2", "2", "3"], {1, 2, 3}),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize(
        "tp, given, expected_errors",
        [
            (set, None, [ErrorFactoryHelper.iterable_required(Loc())]),
            (Set[int], None, [ErrorFactoryHelper.iterable_required(Loc())]),
            (Set[int], [1, "spam"], [ErrorFactoryHelper.integer_required(Loc())]),
        ],
    )
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given, expected_errors):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == tuple(expected_errors)

    class TestInterface:

        @pytest.fixture
        def tp(self):
            return Set[int]

        @pytest.fixture
        def sut(self, parser: IParser, initial, loc):
            return parser(initial, loc)

        @pytest.mark.parametrize(
            "initial, expected_repr",
            [
                (set(), "set()"),
                ({1, "2"}, "{1, 2}"),
            ],
        )
        def test_repr(self, sut: list, expected_repr):
            assert repr(sut) == expected_repr

        @pytest.mark.parametrize(
            "initial, other",
            [
                (set(), set()),
            ],
        )
        def test_check_equality_of_two_sets(self, sut: set, other):
            assert sut == other

        @pytest.mark.parametrize(
            "initial, given, expected",
            [
                (set(), 1, {1}),
                (set(), "2", {2}),
            ],
        )
        def test_when_adding_valid_item_then_it_is_added_after_conversion(self, sut: set, given, expected):
            sut.add(given)
            assert sut == expected

        @pytest.mark.parametrize(
            "initial, given, expected_errors",
            [
                (set(), "foo", [ErrorFactoryHelper.integer_required(Loc())]),
            ],
        )
        def test_when_adding_invalid_item_then_parsing_error_is_raised(self, sut: set, initial, given, expected_errors):
            with pytest.raises(ParsingError) as excinfo:
                sut.add(given)
            assert sut == initial
            assert excinfo.value.errors == tuple(expected_errors)

        @pytest.mark.parametrize(
            "initial, element, expected_result",
            [
                ({1, 2}, 2, {1}),
            ],
        )
        def test_remove_element_from_set(self, sut: set, element, expected_result):
            sut.discard(element)
            assert sut == expected_result


class Dummy(Model):
    value: int


class TestModelParser:

    @pytest.mark.parametrize(
        "tp, given, expected",
        [
            (Dummy, {}, Dummy()),
            (Dummy, Dummy(value=123), Dummy(value=123)),
            (Dummy, {"value": "123"}, Dummy(value=123)),
        ],
    )
    def test_successfully_parse_input_value(self, parser: IParser, loc, given, expected):
        assert parser(given, loc) == expected

    @pytest.mark.parametrize(
        "tp, loc, given, expected_errors",
        [
            (Dummy, Loc(), None, [ErrorFactoryHelper.mapping_required(Loc())]),
            (Dummy, Loc("root"), None, [ErrorFactoryHelper.mapping_required(Loc("root"))]),
            (Dummy, Loc(), {"value": "spam"}, [ErrorFactoryHelper.integer_required(Loc("value"))]),
            (Dummy, Loc("root"), {"value": "spam"}, [ErrorFactoryHelper.integer_required(Loc("root", "value"))]),
        ],
    )
    def test_parsing_fails_if_input_cannot_be_parsed(self, parser: IParser, loc, given, expected_errors):
        result = parser(given, loc)
        assert isinstance(result, Invalid)
        assert result.value == given
        assert result.errors == tuple(expected_errors)
