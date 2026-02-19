from typing import Any, MutableMapping, MutableSequence, MutableSet

import pytest

from mockify.api import _, Return, Invoke

from modelity._parsing.type_proxies import MutableMappingProxy, MutableSequenceProxy, MutableSetProxy
from modelity.base import ModelVisitor, TypeHandler
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType


class NullTypeHandler(TypeHandler):

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        return


class TestMutableMappingProxy:
    UUT = MutableMapping

    @pytest.fixture
    def initial_data(self):
        return {}

    @pytest.fixture
    def key_type_handler(self, type_handler_mock):
        return type_handler_mock.key_type_handler

    @pytest.fixture
    def value_type_handler(self, type_handler_mock):
        return type_handler_mock.value_type_handler

    @pytest.fixture
    def uut(self, initial_data, key_type_handler, value_type_handler):
        return MutableMappingProxy(dict, initial_data, key_type_handler, value_type_handler)

    @pytest.mark.parametrize(
        "initial_data, expected_result",
        [
            ({}, "{}"),
            ({"a": 1, "b": "spam"}, "{'a': 1, 'b': 'spam'}"),
        ],
    )
    def test_repr(self, uut: UUT, expected_result):
        assert repr(uut) == expected_result

    @pytest.mark.parametrize(
        "initial_data, other, expected_status",
        [
            ({}, {}, True),
            ({"a": 1}, {}, False),
            ({"a": 1}, {"a": 1}, True),
            ({"a": 1}, {"a": 2}, False),
            ({"a": 1}, MutableMappingProxy(dict, {"a": 1}, NullTypeHandler(), NullTypeHandler()), True),
            (MutableMappingProxy(dict, {"a": 1}, NullTypeHandler(), NullTypeHandler()), {"a": 1}, True),
        ],
    )
    def test_compare(self, uut: UUT, other, expected_status):
        assert (uut == other) is expected_status

    @pytest.mark.parametrize(
        "initial_data, deleted_key, what_remained",
        [
            ({"a": 1}, "a", {}),
            ({"a": 1, "b": "spam"}, "b", {"a": 1}),
        ],
    )
    def test_delete_existing_item(self, uut: UUT, deleted_key, what_remained):
        del uut[deleted_key]
        assert uut == what_remained

    def test_setting_item_invokes_key_and_value_type_handlers(self, uut: UUT, key_type_handler, value_type_handler):
        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "one").will_once(Return("one"))
        value_type_handler.parse.expect_call(_, Loc("one"), "1").will_once(Return(1))
        uut["one"] = "1"
        assert uut["one"] == 1

    def test_when_key_parsing_fails_then_value_is_not_parsed_and_setting_key_raises_error(
        self, uut: UUT, key_type_handler, value_type_handler
    ):

        def parse(errors: list[Error], loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, int))
            return Unset

        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "one").will_once(Invoke(parse))
        value_type_handler.parse.expect_call(_, _, "1").times(0)
        with pytest.raises(ParsingError) as excinfo:
            uut["one"] = "1"
        assert excinfo.value.errors == tuple([ErrorFactory.parse_error(Loc.irrelevant(), "one", int)])

    def test_when_value_parsing_fails_then_setting_key_raises_error(
        self, uut: UUT, key_type_handler, value_type_handler
    ):

        def parse(errors: list[Error], loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, int))
            return Unset

        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "one").will_once(Return("one"))
        value_type_handler.parse.expect_call(_, Loc("one"), "foo").will_once(Invoke(parse))
        with pytest.raises(ParsingError) as excinfo:
            uut["one"] = "foo"
        assert excinfo.value.errors == tuple([ErrorFactory.parse_error(Loc("one"), "foo", int)])

    @pytest.mark.parametrize(
        "initial_data, expected_result",
        [
            ({}, []),
            ({"a": 1, "b": 2}, ["a", "b"]),
        ],
    )
    def test_iter(self, uut: UUT, expected_result):
        assert list(x for x in uut) == expected_result

    @pytest.mark.parametrize(
        "initial_data, expected_result",
        [
            ({}, 0),
            ({"a": 1}, 1),
            ({"a": 1, "b": 2, "c": 3}, 3),
        ],
    )
    def test_len(self, uut: UUT, expected_result):
        assert len(uut) == expected_result

    def test_setdefault_with_one_arg(self, uut: UUT, key_type_handler, value_type_handler):
        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "one").will_once(Return("one"))
        value_type_handler.parse.expect_call(_, Loc("one"), None).will_once(Return(None))
        assert uut.setdefault("one") is None
        assert uut == {"one": None}

    def test_setdefault_with_two_args(self, uut: UUT, key_type_handler, value_type_handler):
        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "one").will_once(Return("one"))
        value_type_handler.parse.expect_call(_, Loc("one"), 123).will_once(Return(123))
        assert uut.setdefault("one", 123) == 123
        assert uut == {"one": 123}

    @pytest.mark.parametrize(
        "initial_data, key, expected_value",
        [
            ({"one": 1}, "one", 1),
        ],
    )
    def test_setdefault_returns_existing_key(self, uut: UUT, key, expected_value):
        assert uut.setdefault(key) == expected_value

    def test_update_from_mapping(self, uut: UUT, key_type_handler, value_type_handler):
        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "one").will_once(Return("one"))
        value_type_handler.parse.expect_call(_, Loc("one"), 1).will_once(Return(1))
        uut.update({"one": 1})
        assert uut == {"one": 1}

    def test_update_from_iterable(self, uut: UUT, key_type_handler, value_type_handler):
        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "one").will_once(Return("one"))
        value_type_handler.parse.expect_call(_, Loc("one"), 1).will_once(Return(1))
        uut.update([("one", 1)])
        assert uut == {"one": 1}

    def test_update_from_mapping_and_kwargs(self, uut: UUT, key_type_handler, value_type_handler):
        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "one").will_once(Return("one"))
        value_type_handler.parse.expect_call(_, Loc("one"), 1).will_once(Return(1))
        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "two").will_once(Return("two"))
        value_type_handler.parse.expect_call(_, Loc("two"), 2).will_once(Return(2))
        uut.update({"one": 1}, two=2)
        assert uut == {"one": 1, "two": 2}

    def test_update_from_iterable_and_kwargs(self, uut: UUT, key_type_handler, value_type_handler):
        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "one").will_once(Return("one"))
        value_type_handler.parse.expect_call(_, Loc("one"), 1).will_once(Return(1))
        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "two").will_once(Return("two"))
        value_type_handler.parse.expect_call(_, Loc("two"), 2).will_once(Return(2))
        uut.update([("one", 1)], two=2)
        assert uut == {"one": 1, "two": 2}

    def test_update_from_kwargs(self, uut: UUT, key_type_handler, value_type_handler):
        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "one").will_once(Return("one"))
        value_type_handler.parse.expect_call(_, Loc("one"), 1).will_once(Return(1))
        uut.update(one=1)
        assert uut == {"one": 1}

    def test_when_update_fails_then_error_raised(self, uut: UUT, key_type_handler, value_type_handler):

        def parse(errors: list[Error], loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, int))
            return Unset

        key_type_handler.parse.expect_call(_, Loc.irrelevant(), "one").will_once(Return("one"))
        value_type_handler.parse.expect_call(_, Loc("one"), "spam").will_once(Invoke(parse))
        with pytest.raises(ParsingError) as excinfo:
            uut.update(one="spam")
        assert excinfo.value.errors == tuple([ErrorFactory.parse_error(Loc("one"), "spam", int)])


class TestMutableSequenceProxy:
    UUT = MutableSequence

    @pytest.fixture
    def typ(self):
        return list

    @pytest.fixture
    def target(self):
        return []

    @pytest.fixture
    def uut(self, typ, target, type_handler_mock):
        return MutableSequenceProxy(typ, target, type_handler_mock)

    @pytest.mark.parametrize(
        "target, expected_repr",
        [
            ([], "[]"),
        ],
    )
    def test_repr(self, uut: UUT, expected_repr):
        assert repr(uut) == expected_repr

    @pytest.mark.parametrize(
        "target, expected_repr",
        [
            ([], 0),
            ([1], 1),
            ([1, 2, 3], 3),
        ],
    )
    def test_len(self, uut: UUT, expected_repr):
        assert len(uut) == expected_repr

    @pytest.mark.parametrize(
        "target, other, expected_status",
        [
            ([], [], True),
            ([], [1], False),
            ([1], [1], True),
        ],
    )
    def test_compare(self, uut: UUT, other, expected_status):
        assert (uut == other) is expected_status

    @pytest.mark.parametrize(
        "target, index, expected_result",
        [
            ([1, 2, 3], 0, [2, 3]),
            ([1, 2, 3], -1, [1, 2]),
        ],
    )
    def test_delitem(self, uut: UUT, index, expected_result):
        del uut[index]
        assert uut == expected_result

    @pytest.mark.parametrize(
        "target, index, expected_result",
        [
            ([1, 2, 3], 0, 1),
            ([1, 2, 3], -1, 3),
        ],
    )
    def test_getitem(self, uut: UUT, index, expected_result):
        assert uut[index] == expected_result

    @pytest.mark.parametrize(
        "target, index, input_value, output_value, expected_result",
        [
            ([1, 2, 3], 0, "10", 10, [10, 2, 3]),
            ([1, 2, 3], 1, "10", 10, [1, 10, 3]),
        ],
    )
    def test_set_item_with_successful_parsing(
        self, uut: UUT, index, input_value, output_value, expected_result, type_handler_mock
    ):
        type_handler_mock.parse.expect_call(_, Loc(index), input_value).will_once(Return(output_value))
        uut[index] = input_value
        assert uut == expected_result

    @pytest.mark.parametrize(
        "target, index, input_value, output_value, expected_result",
        [
            ([1, 2, 3], 0, "10", 10, [10, 1, 2, 3]),
            ([1, 2, 3], 1, "10", 10, [1, 10, 2, 3]),
        ],
    )
    def test_insert_item_with_successful_parsing(
        self, uut: UUT, index, input_value, output_value, expected_result, type_handler_mock
    ):
        type_handler_mock.parse.expect_call(_, Loc(index), input_value).will_once(Return(output_value))
        uut.insert(index, input_value)
        assert uut == expected_result

    @pytest.mark.parametrize(
        "target, index, input_value",
        [
            ([1, 2, 3], 0, "not an int"),
        ],
    )
    def test_set_item_with_failed_parsing(self, uut: UUT, typ, index, input_value, type_handler_mock):
        def parse(errors: list, loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, int))
            return Unset

        type_handler_mock.parse.expect_call(_, Loc(index), input_value).will_once(Invoke(parse))
        with pytest.raises(ParsingError) as excinfo:
            uut[index] = input_value
        assert excinfo.value.typ == typ
        assert excinfo.value.errors == tuple([ErrorFactory.parse_error(Loc(index), input_value, int)])

    @pytest.mark.parametrize("target", [[], [1, 2, 3]])
    def test_extend_successfully(self, uut: UUT, type_handler_mock, target):
        type_handler_mock.parse.expect_call(_, Loc(0), 1).will_once(Return(1))
        type_handler_mock.parse.expect_call(_, Loc(1), "2").will_once(Return(2))
        type_handler_mock.parse.expect_call(_, Loc(2), 3).will_once(Return(3))
        target_before = list(target)
        uut.extend([1, "2", 3])
        assert uut == target_before + [1, 2, 3]

    @pytest.mark.parametrize(
        "target",
        [
            [],
            [1, 2, 3],
        ],
    )
    def test_when_extend_fails_it_collects_errors(self, uut: UUT, type_handler_mock, typ, target):
        def parse(errors: list, loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, int))
            return Unset

        type_handler_mock.parse.expect_call(_, Loc(0), 1).will_once(Return(1))
        type_handler_mock.parse.expect_call(_, Loc(1), "spam").will_once(Invoke(parse))
        type_handler_mock.parse.expect_call(_, Loc(2), 3).will_once(Return(3))
        type_handler_mock.parse.expect_call(_, Loc(3), "more spam").will_once(Invoke(parse))
        target_before = list(target)
        with pytest.raises(ParsingError) as excinfo:
            uut.extend([1, "spam", 3, "more spam"])
        assert uut == target_before
        assert excinfo.value.typ == typ
        assert excinfo.value.errors == tuple(
            [
                ErrorFactory.parse_error(Loc(1), "spam", int),
                ErrorFactory.parse_error(Loc(3), "more spam", int),
            ]
        )


class TestMutableSetProxy:
    UUT = MutableSet

    @pytest.fixture
    def typ(self):
        return set

    @pytest.fixture
    def target(self):
        return set()

    @pytest.fixture
    def uut(self, typ, target, type_handler_mock):
        return MutableSetProxy(typ, target, type_handler_mock)

    @pytest.mark.parametrize(
        "target, expected_repr",
        [
            (set(), "set()"),
            (set([1, 2]), "{1, 2}"),
        ],
    )
    def test_repr(self, uut, expected_repr):
        assert repr(uut) == expected_repr

    @pytest.mark.parametrize(
        "target, other, expected_status",
        [
            (set(), set(), True),
            (set(), {1}, False),
            ({1}, {1}, True),
        ],
    )
    def test_compare(self, uut: UUT, other, expected_status):
        assert (uut == other) is expected_status

    @pytest.mark.parametrize(
        "target, value, expected_status",
        [
            (set(), 1, False),
            (set([1, 2]), 1, True),
        ],
    )
    def test_contains(self, uut, value, expected_status):
        assert (value in uut) == expected_status

    @pytest.mark.parametrize(
        "target, expected_result",
        [
            (set(), []),
            (set([1, 2]), [1, 2]),
        ],
    )
    def test_iter(self, uut, expected_result):
        assert list(uut) == expected_result

    @pytest.mark.parametrize(
        "target, expected_result",
        [
            (set(), 0),
            (set([1, 2]), 2),
        ],
    )
    def test_len(self, uut, expected_result):
        assert len(uut) == expected_result

    @pytest.mark.parametrize(
        "target, input_value, output_value, expected_result",
        [
            (set(), 1, 1, {1}),
            ({1}, 1, 1, {1}),
            ({1, 2}, "3", 3, {1, 2, 3}),
        ],
    )
    def test_add_successfully(self, uut: UUT, input_value, output_value, expected_result, type_handler_mock):
        type_handler_mock.parse.expect_call(_, Loc.irrelevant(), input_value).will_once(Return(output_value))
        uut.add(input_value)
        assert output_value in uut
        assert uut == expected_result

    @pytest.mark.parametrize(
        "target, input_value, expected_result",
        [
            (set(), "spam", set()),
            ({1, 2}, "spam", {1, 2}),
        ],
    )
    def test_add_fails_with_parsing_error(self, uut: UUT, input_value, expected_result, typ, type_handler_mock):
        def parse(errors: list, loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, int))
            return Unset

        type_handler_mock.parse.expect_call(_, Loc.irrelevant(), input_value).will_once(Invoke(parse))
        with pytest.raises(ParsingError) as excinfo:
            uut.add(input_value)
        assert uut == expected_result
        assert excinfo.value.typ == typ
        assert excinfo.value.errors == tuple([ErrorFactory.parse_error(Loc.irrelevant(), input_value, int)])

    @pytest.mark.parametrize(
        "target, input_value, output_value, expected_result",
        [
            ({1, 2}, 1, 1, {2}),
            ({1, 2, 3}, "2", 2, {1, 3}),
            (set(), 1, 1, set()),
        ],
    )
    def test_discard(self, uut: UUT, input_value, output_value, expected_result, type_handler_mock):
        type_handler_mock.parse.expect_call(_, Loc.irrelevant(), input_value).will_once(Return(output_value))
        uut.add(input_value)
        uut.discard(output_value)
        assert uut == expected_result

    def test_update_successfully(self, uut: UUT, type_handler_mock):
        type_handler_mock.parse.expect_call(_, Loc.irrelevant(), 1).will_once(Return(1))
        type_handler_mock.parse.expect_call(_, Loc.irrelevant(), "2").will_once(Return(2))
        type_handler_mock.parse.expect_call(_, Loc.irrelevant(), 3).will_once(Return(3))
        uut |= {1, "2", 3}
        assert uut == {1, 2, 3}

    @pytest.mark.parametrize(
        "target",
        [
            set(),
            {5, 6},
        ],
    )
    def test_update_with_parsing_error(self, uut: UUT, type_handler_mock, target, typ):
        def parse(errors: list, loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, int))
            return Unset

        type_handler_mock.parse.expect_call(_, Loc.irrelevant(), 1).will_once(Return(1))
        type_handler_mock.parse.expect_call(_, Loc.irrelevant(), "spam").will_once(Invoke(parse))
        type_handler_mock.parse.expect_call(_, Loc.irrelevant(), "more spam").will_once(Invoke(parse))
        type_handler_mock.parse.expect_call(_, Loc.irrelevant(), 2).will_once(Return(2))
        target_before = set(target)
        with pytest.raises(ParsingError) as excinfo:
            uut |= {1, "spam", "more spam", 2}
        assert uut == target_before
        assert excinfo.value.typ == typ
        assert len(excinfo.value.errors) == 2

    def test_or(self, uut: UUT):
        foo = uut | {1, 2}
        assert foo == {1, 2}

    @pytest.mark.parametrize(
        "target, other, expected",
        [
            (set(), set(), set()),
            ({1, 2}, {2, 3}, {2}),
            ({1, 2, 3}, {4, 5}, set()),
        ],
    )
    def test_intersection(self, uut: UUT, other, expected):
        result = uut & set(other)
        assert result == expected

    @pytest.mark.parametrize(
        "target, other, expected",
        [
            (set(), set(), set()),
            ({1, 2}, {2, 3}, {1}),
            ({1, 2, 3}, {2}, {1, 3}),
        ],
    )
    def test_difference(self, uut: UUT, other, expected):
        result = uut - set(other)
        assert result == expected

    @pytest.mark.parametrize(
        "target, other, expected",
        [
            (set(), set(), set()),
            ({1, 2}, {2, 3}, {1, 3}),
            ({1, 2, 3}, {2}, {1, 3}),
        ],
    )
    def test_symmetric_difference(self, uut: UUT, other, expected):
        result = uut ^ set(other)
        assert result == expected

    @pytest.mark.parametrize(
        "target, other, expected",
        [
            (set(), set(), True),
            (set(), {1}, True),
            ({1}, {1, 2}, True),
            ({1, 2}, {1, 2}, True),
            ({1, 2, 3}, {1, 2}, False),
        ],
    )
    def test_issubset(self, uut: UUT, other, expected):
        assert (uut <= set(other)) is expected

    @pytest.mark.parametrize(
        "target, other, expected",
        [
            (set(), set(), True),
            ({1}, set(), True),
            ({1, 2}, {1}, True),
            ({1, 2}, {1, 2}, True),
            ({1, 2}, {1, 2, 3}, False),
        ],
    )
    def test_issuperset(self, uut: UUT, other, expected):
        assert (uut >= set(other)) is expected

    @pytest.mark.parametrize(
        "target, other, expected",
        [
            (set(), set(), False),
            (set(), {1}, True),
            ({1}, {1, 2}, True),
            ({1, 2}, {1, 2}, False),
            ({1, 2, 3}, {1, 2}, False),
        ],
    )
    def test_proper_subset(self, uut: UUT, other, expected):
        assert (uut < set(other)) is expected

    @pytest.mark.parametrize(
        "target, other, expected",
        [
            (set(), set(), False),
            ({1}, set(), True),
            ({1, 2}, {1}, True),
            ({1, 2}, {1, 2}, False),
            ({1, 2}, {1, 2, 3}, False),
        ],
    )
    def test_proper_superset(self, uut: UUT, other, expected):
        assert (uut > set(other)) is expected
