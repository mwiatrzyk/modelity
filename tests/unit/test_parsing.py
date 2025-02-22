from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated, Any, Iterable, Literal, Optional, Union, get_args

from modelity.constraints import Ge, Gt, Le, Lt, MaxLen, MinLen, Regex
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.loc import Loc
from modelity.parsing.main import make_parser
from modelity.unset import Unset

import pytest

loc = Loc("foo")


@pytest.fixture
def errors():
    return []


class TestAnyParsing:

    @pytest.fixture
    def parser(self):
        return make_parser(Any)

    @pytest.mark.parametrize(
        "value",
        [
            1,
            3.14,
            "foo",
            [],
            {},
            set(),
            tuple(),
        ],
    )
    def test_parsing(self, parser, errors, value):
        assert parser(errors, loc, value) is value
        assert errors == []


class TestBoolParsing:

    @pytest.fixture
    def parser(self, true_literals, false_literals):
        return make_parser(bool, true_literals=true_literals, false_literals=false_literals)

    @pytest.mark.parametrize(
        "true_literals, false_literals, value, expected_result, expected_errors",
        [
            (None, None, True, True, []),
            (None, None, 1, True, []),
            (None, None, "True", True, []),
            (None, None, False, False, []),
            (None, None, 0, False, []),
            (None, None, "False", False, []),
            (["y"], ["n"], "y", True, []),
            (["y"], ["n"], "n", False, []),
            (None, None, 3.14, Unset, [ErrorFactory.boolean_required(loc, 3.14)]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestDateTimeParsing:

    @pytest.fixture
    def parser(self, formats):
        return make_parser(datetime, formats=formats)

    @pytest.mark.parametrize(
        "formats, value, expected_result, expected_errors",
        [
            (None, datetime(2025, 2, 22, 10, 11, 22), datetime(2025, 2, 22, 10, 11, 22), []),
            (None, "2025-02-22T10:11:22", datetime(2025, 2, 22, 10, 11, 22), []),
            (None, "2025-02-22T10:11:22+00:00", datetime(2025, 2, 22, 10, 11, 22, tzinfo=timezone.utc), []),
            (
                None,
                "2025-02-22T10:11:22+02:00",
                datetime(2025, 2, 22, 10, 11, 22, tzinfo=timezone(timedelta(seconds=7200))),
                [],
            ),
            (None, "20250222101122", datetime(2025, 2, 22, 10, 11, 22), []),
            (None, "20250222101122+0000", datetime(2025, 2, 22, 10, 11, 22, tzinfo=timezone.utc), []),
            (
                None,
                "20250222101122+0200",
                datetime(2025, 2, 22, 10, 11, 22, tzinfo=timezone(timedelta(seconds=7200))),
                [],
            ),
            (None, "2025-02-22", datetime(2025, 2, 22), []),
            (None, "20250222", datetime(2025, 2, 22), []),
            (["%d-%m-%Y"], "22-02-2025", datetime(2025, 2, 22), []),
            (None, 123, Unset, [ErrorFactory.datetime_required(loc, 123)]),
            (["%Y-%m-%d"], "spam", Unset, [ErrorFactory.unsupported_datetime_format(loc, ["%Y-%m-%d"], "spam")]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestEnumParsing:

    class Dummy(Enum):
        FOO = 1
        BAR = 2
        BAZ = 3

    @pytest.fixture
    def parser(self):
        return make_parser(self.Dummy)

    @pytest.mark.parametrize(
        "value, expected_result, expected_errors",
        [
            (Dummy.FOO, Dummy.FOO, []),
            (Dummy.BAR, Dummy.BAR, []),
            (Dummy.BAZ, Dummy.BAZ, []),
            (1, Dummy.FOO, []),
            (2, Dummy.BAR, []),
            (3, Dummy.BAZ, []),
            (4, Unset, [ErrorFactory.invalid_enum(loc, Dummy, 4)]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestLiteralParser:
    Dummy = Literal[1, 3.14, "spam"]

    allowed_values = get_args(Dummy)

    @pytest.fixture
    def parser(self):
        return make_parser(self.Dummy)

    @pytest.mark.parametrize(
        "value, expected_result, expected_errors",
        [
            (1, 1, []),
            (3.14, 3.14, []),
            ("spam", "spam", []),
            ("1", Unset, [ErrorFactory.invalid_literal(loc, allowed_values, "1")]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestNoneParser:

    @pytest.fixture
    def parser(self):
        return make_parser(type(None))

    @pytest.mark.parametrize(
        "value, expected_result, expected_errors",
        [
            (None, None, []),
            ("spam", Unset, [ErrorFactory.none_required(loc, "spam")]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestIntegerParser:

    @pytest.fixture
    def parser(self):
        return make_parser(int)

    @pytest.mark.parametrize(
        "value, expected_result, expected_errors",
        [
            (1, 1, []),
            ("2", 2, []),
            ("spam", Unset, [ErrorFactory.integer_required(loc, "spam")]),
            (None, Unset, [ErrorFactory.integer_required(loc, None)]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestFloatParser:

    @pytest.fixture
    def parser(self):
        return make_parser(float)

    @pytest.mark.parametrize(
        "value, expected_result, expected_errors",
        [
            (1, 1, []),
            ("2", 2, []),
            ("3.14", 3.14, []),
            ("spam", Unset, [ErrorFactory.float_required(loc, "spam")]),
            (None, Unset, [ErrorFactory.float_required(loc, None)]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestStrParser:

    @pytest.fixture
    def parser(self, encodings):
        return make_parser(str, encodings=encodings)

    @pytest.mark.parametrize(
        "encodings, value, expected_result, expected_errors",
        [
            (None, "spam", "spam", []),
            (None, b"more spam", "more spam", []),
            (["ascii"], b"more spam", "more spam", []),
            (["ascii", "utf-8"], b"\xff", Unset, [ErrorFactory.unicode_decode_error(loc, ["ascii", "utf-8"], b"\xff")]),
            (None, 123, Unset, [ErrorFactory.string_required(loc, 123)]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestBytesParser:

    @pytest.fixture
    def parser(self, encoding):
        return make_parser(bytes, encoding=encoding)

    @pytest.mark.parametrize(
        "encoding, value, expected_result, expected_errors",
        [
            (None, "spam", b"spam", []),
            (None, b"more spam", b"more spam", []),
            ("ascii", "spam", b"spam", []),
            (None, 123, Unset, [ErrorFactory.bytes_required(loc, 123)]),
            ("ascii", "ąść", Unset, [ErrorFactory.unicode_encode_error(loc, "ąść", "ascii")]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestAnnotatedParser:

    @pytest.fixture
    def parser(self, typ):
        return make_parser(typ)

    @pytest.mark.parametrize(
        "typ, value, expected_result, expected_errors",
        [
            (Annotated[int, Ge(0), Le(5)], "0", 0, []),
            (Annotated[int, Ge(0), Le(5)], "5", 5, []),
            (Annotated[int, Ge(0), Le(5)], -1, Unset, [ErrorFactory.ge_failed(loc, -1, 0)]),
            (Annotated[int, Ge(0), Le(5)], 6, Unset, [ErrorFactory.le_failed(loc, 6, 5)]),
            (Annotated[float, Gt(0), Lt(1)], 0.5, 0.5, []),
            (Annotated[float, Gt(0), Lt(1)], 0, Unset, [ErrorFactory.gt_failed(loc, 0, 0)]),
            (Annotated[float, Gt(0), Lt(1)], 1, Unset, [ErrorFactory.lt_failed(loc, 1, 1)]),
            (Annotated[str, MinLen(1), MaxLen(5)], "a", "a", []),
            (Annotated[str, MinLen(1), MaxLen(5)], "12345", "12345", []),
            (Annotated[str, MinLen(1), MaxLen(5)], "", Unset, [ErrorFactory.min_len_failed(loc, "", 1)]),
            (
                Annotated[str, MinLen(1), MaxLen(5)],
                "spam more spam",
                Unset,
                [ErrorFactory.max_len_failed(loc, "spam more spam", 5)],
            ),
            (Annotated[str, Regex("^[a-z]+$")], "abc", "abc", []),
            (Annotated[str, Regex("^[a-z]+$")], "123", Unset, [ErrorFactory.regex_failed(loc, "123", "^[a-z]+$")]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestUnionParser:

    @pytest.fixture
    def parser(self, typ):
        return make_parser(typ)

    @pytest.mark.parametrize(
        "typ, value, expected_result, expected_errors",
        [
            (Optional[str], "spam", "spam", []),
            (Optional[str], None, None, []),
            (Optional[str], 123, Unset, [ErrorFactory.string_required(loc, 123)]),
            (Union[int, str], "spam", "spam", []),
            (Union[int, str], "123", "123", []),
            (Union[int, str], 123, 123, []),
            (
                Union[int, str],
                None,
                Unset,
                [
                    ErrorFactory.integer_required(loc, None),
                    ErrorFactory.string_required(loc, None),
                    ErrorFactory.union_parsing_failed(loc, None, [int, str]),
                ],
            ),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestTupleParser:

    @pytest.fixture
    def parser(self, typ):
        return make_parser(typ)

    @pytest.mark.parametrize(
        "typ, value, expected_result, expected_errors",
        [
            (tuple, [], tuple(), []),
            (tuple, "foo", tuple(["f", "o", "o"]), []),
            (tuple, 123, Unset, [ErrorFactory.unsupported_type(loc, [Iterable], 123)]),
            (tuple[int, ...], "1", tuple([1]), []),
            (tuple[int, ...], "123", tuple([1, 2, 3]), []),
            (tuple[int, ...], "1a2", Unset, [ErrorFactory.integer_required(loc + Loc(1), "a")]),
            (tuple[int, float, str], [1, "3.14", "spam"], tuple([1, 3.14, "spam"]), []),
            (
                tuple[int, float, str],
                ["foo", "3.14", "spam"],
                Unset,
                [ErrorFactory.integer_required(loc + Loc(0), "foo")],
            ),
            (
                tuple[int, float, str],
                [1, "3.14"],
                Unset,
                [ErrorFactory.tuple_too_short(loc, (1, "3.14"), 3)],
            ),
            (
                tuple[int, float, str],
                [1, "3.14", "spam", "more spam"],
                Unset,
                [ErrorFactory.tuple_too_long(loc, (1, "3.14", "spam", "more spam"), 3)],
            ),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors


class TestDictParser:

    @pytest.fixture
    def typ(self):
        return dict[int, float]

    @pytest.fixture
    def value(self):
        return {}

    @pytest.fixture
    def parser(self, typ):
        return make_parser(typ)

    @pytest.fixture
    def out(self, parser, errors, value):
        return parser(errors, loc, value)

    @pytest.mark.parametrize(
        "typ, value, expected_result, expected_errors",
        [
            (dict, [], {}, []),
            (dict, [(1, "one")], {1: "one"}, []),
            (dict, {}, {}, []),
            (dict, "foo", Unset, [ErrorFactory.mapping_required(loc, "foo")]),
            (dict, 123, Unset, [ErrorFactory.mapping_required(loc, 123)]),
            (dict[str, int], [], {}, []),
            (dict[str, int], {"foo": "123"}, {"foo": 123}, []),
            (dict[str, int], {1: 2}, Unset, [ErrorFactory.string_required(loc, 1)]),
            (
                dict[str, int],
                {1: "two"},
                Unset,
                [ErrorFactory.string_required(loc, 1), ErrorFactory.integer_required(loc + Loc(1), "two")],
            ),
            (dict[str, int], {"two": "two"}, Unset, [ErrorFactory.integer_required(loc + Loc("two"), "two")]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "value, expected_repr",
        [
            ({}, "{}"),
            ({"1": "3.14"}, "{1: 3.14}"),
        ],
    )
    def test_repr(self, out, expected_repr):
        assert repr(out) == expected_repr

    @pytest.mark.parametrize(
        "typ, a, b, is_same",
        [
            (dict, {}, {}, True),
            (dict, {1: 2}, {}, False),
            (dict, {1: 2}, {2: 1}, False),
            (dict, {1: 2}, {1: 2}, True),
            (dict[int, int], {}, {}, True),
            (dict[int, int], {1: 2}, {}, False),
            (dict[int, int], {1: 2}, {2: 1}, False),
            (dict[int, int], {1: 2}, {1: 2}, True),
        ],
    )
    def test_eq(self, parser, errors, a, b, is_same):
        assert (parser(errors, loc, a) == parser(errors, loc, b)) is is_same

    def test_setting_item_converts_keys(self, out: dict):
        out["123"] = 3.14
        assert list(out) == [123]
        assert out[123] == 3.14

    def test_setting_item_converts_values(self, out: dict):
        out[1] = "3.14"
        assert list(out) == [1]
        assert out[1] == 3.14

    def test_parsing_error_is_raised_when_setting_invalid_key(self, out: dict):
        with pytest.raises(ParsingError) as excinfo:
            out["spam"] = 3.14
        assert excinfo.value.errors == tuple([ErrorFactory.integer_required(loc, "spam")])

    def test_parsing_error_is_raised_when_setting_invalid_value(self, out: dict):
        with pytest.raises(ParsingError) as excinfo:
            out[123] = "spam"
        assert excinfo.value.errors == tuple([ErrorFactory.float_required(loc + Loc(123), "spam")])

    def test_set_item_and_delete_it(self, out: dict):
        out[1] = 2
        assert out[1] == 2
        del out[1]
        assert list(out) == []

    def test_check_length(self, out: dict):
        assert len(out) == 0
        out[1] = 3.14
        assert len(out) == 1
        del out[1]
        assert len(out) == 0


class TestListParser:

    @pytest.fixture
    def parser(self, typ):
        return make_parser(typ)

    @pytest.mark.parametrize(
        "typ, value, expected_result, expected_errors",
        [
            (list, [], [], []),
            (list, "123", ["1", "2", "3"], []),
            (list, None, Unset, [ErrorFactory.iterable_required(loc, None)]),
            (list, 123, Unset, [ErrorFactory.iterable_required(loc, 123)]),
            (list[int], ["123"], [123], []),
            (list[int], ["1", 2, "3"], [1, 2, 3], []),
            (list[int], 123, Unset, [ErrorFactory.iterable_required(loc, 123)]),
            (list[int], ["1", "2", "spam"], Unset, [ErrorFactory.integer_required(loc + Loc(2), "spam")]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ, value, expected_repr",
        [
            (list, [], "[]"),
            (list, [1, "2"], "[1, '2']"),
            (list[int], [1, "2"], "[1, 2]"),
        ],
    )
    def test_repr(self, parser, errors, value, expected_repr):
        assert repr(parser(errors, loc, value)) == expected_repr

    @pytest.mark.parametrize(
        "typ, a, b, is_same",
        [
            (list, [], [], True),
            (list, [1], [], False),
            (list, [1], [2], False),
            (list, [1], [1], True),
            (list[int], [], [], True),
            (list[int], [1], [], False),
            (list[int], [1], [2], False),
            (list[int], [1], [1], True),
        ],
    )
    def test_eq(self, parser, errors, a, b, is_same):
        assert (parser(errors, loc, a) == parser(errors, loc, b)) is is_same

    @pytest.mark.parametrize("typ", [list[int]])
    def test_setting_getting_and_deleting_items(self, parser, errors):
        l = parser(errors, loc, [1])
        assert len(l) == 1
        assert l[0] == 1
        l[0] = "2"
        assert l[0] == 2
        del l[0]
        assert len(l) == 0

    @pytest.mark.parametrize("typ", [list[int]])
    def test_inserting_or_appending_items(self, parser, errors):
        l = parser(errors, loc, [1])
        assert l == [1]
        l.insert(0, "123")
        assert l == [123, 1]
        l.append("4")
        assert l == [123, 1, 4]

    @pytest.mark.parametrize(
        "typ, initial, index, value, expected_errors",
        [
            (list[int], [1], 0, "spam", [ErrorFactory.integer_required(loc + Loc(0), "spam")]),
        ],
    )
    def test_setting_to_invalid_value_causes_parsing_error(
        self, parser, errors, initial, index, value, expected_errors
    ):
        l = parser(errors, loc, initial)
        with pytest.raises(ParsingError) as excinfo:
            l[index] = value
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "typ, initial, index, value, expected_errors",
        [
            (list[int], [1], 0, "spam", [ErrorFactory.integer_required(loc + Loc(0), "spam")]),
        ],
    )
    def test_inserting_invalid_value_causes_parsing_error(self, parser, errors, initial, index, value, expected_errors):
        l = parser(errors, loc, initial)
        with pytest.raises(ParsingError) as excinfo:
            l.insert(index, value)
        assert excinfo.value.errors == tuple(expected_errors)


class TestSetParser:

    @pytest.fixture
    def parser(self, typ):
        return make_parser(typ)

    @pytest.mark.parametrize(
        "typ, value, expected_result, expected_errors",
        [
            (set, [], set(), []),
            (set, "123", {"1", "2", "3"}, []),
            (set, [1, 3.14, "spam"], {1, 3.14, "spam"}, []),
            (set, 123, Unset, [ErrorFactory.iterable_required(loc, 123)]),
            (set, [[123]], Unset, [ErrorFactory.hashable_required(loc, [[123]])]),
            (set[int], [1, 2, "3", 3, "4"], {1, 2, 3, 4}, []),
            (set[int], 123, Unset, [ErrorFactory.iterable_required(loc, 123)]),
        ],
    )
    def test_parsing(self, parser, errors, value, expected_result, expected_errors):
        assert parser(errors, loc, value) == expected_result
        assert errors == expected_errors

    @pytest.mark.parametrize("typ", [set[list], set[123]])
    def test_making_set_with_non_type_causes_type_error(self, typ):
        with pytest.raises(TypeError) as excinfo:
            make_parser(typ)
        assert str(excinfo.value) == "'T' must be hashable type to be used with 'set[T]' generic type"

    @pytest.mark.parametrize(
        "typ, value, expected_repr",
        [
            (set, [], "set()"),
            (set, ["2"], "{'2'}"),
            (set[int], ["2"], "{2}"),
        ],
    )
    def test_repr(self, parser, errors, value, expected_repr):
        assert repr(parser(errors, loc, value)) == expected_repr

    @pytest.mark.parametrize(
        "typ, a, b, is_same",
        [
            (set, [], [], True),
            (set, [1, 1, 1], [1], True),
            (set[int], ["123"], [123], True),
        ],
    )
    def test_eq(self, parser, errors, a, b, is_same):
        assert (parser(errors, loc, a) == parser(errors, loc, b)) is is_same

    def test_adding_item_converts_it_according_to_item_type(self, errors):
        parser = make_parser(set[int])
        s = parser(errors, loc, [])
        s.add("123")
        assert s == {123}

    def test_adding_invalid_item_causes_parsing_error(self, errors):
        parser = make_parser(set[int])
        s = parser(errors, loc, [])
        with pytest.raises(ParsingError) as excinfo:
            s.add("dummy")
        assert excinfo.value.errors == tuple([ErrorFactory.integer_required(loc, "dummy")])

    def test_add_value_and_discard_it(self, errors):
        parser = make_parser(set[int])
        s = parser(errors, loc, [])
        s.add("123")
        assert s == {123}
        s.discard(123)
        assert s == set()

    def test_contains_and_len(self, errors):
        parser = make_parser(set[int])
        s = parser(errors, loc, [])
        assert s is not Unset
        assert 123 not in s
        assert len(s) == 0
        s.add("123")
        assert 123 in s
        assert len(s) == 1
        s.discard(123)
        assert len(s) == 0

    def test_iter(self, errors):
        parser = make_parser(set[int])
        s = parser(errors, loc, [])
        assert list(s) == []
        s.add(1)
        s.add(2)
        s.add("3")
        assert list(s) == [1, 2, 3]
