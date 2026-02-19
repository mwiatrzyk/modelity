from typing import Any, MutableSet, Sequence, Set, get_args

import pytest

from mockify.api import Return, Invoke

from modelity._parsing.type_handlers.set import AnyMutableSetTypeHandler, TypedMutableSetTypeHandler
from modelity.base import TypeHandler
from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset

from .common import loc


class TestAnyMutableSetTypeHandler:
    UUT = TypeHandler

    @pytest.fixture
    def uut(self, typ):
        return AnyMutableSetTypeHandler(typ)

    @pytest.mark.parametrize(
        "typ, expected_error",
        [
            (int, "unsupported type; got <class 'int'>, expected MutableSet"),
            (dict[str, int], "unsupported type; got dict[str, int], expected MutableSet"),
            (set[int], "unsupported type; got set[int], expected one of: MutableSet, MutableSet[Any]"),
        ],
    )
    def test_constructing_fails_for_unsupported_type(self, typ, expected_error):
        with pytest.raises(TypeError) as excinfo:
            AnyMutableSetTypeHandler(typ)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "typ, input_value, output_value",
        [
            (set, set(), set()),
            (set, [], set()),
            (set, {1, 2}, {1, 2}),
            (set, [1, 1, 2], {1, 2}),
            (set, [], set()),
            (set, {1, 2}, {1, 2}),
            (set, [1, 1, 2], {1, 2}),
            (set[Any], [1, 3.14, "spam"], {1, 3.14, "spam"}),
            (MutableSet, [1, 3.14, "spam"], {1, 3.14, "spam"}),
            (MutableSet[Any], [1, 3.14, "spam"], {1, 3.14, "spam"}),
        ],
    )
    def test_parse_successfully(self, uut: UUT, input_value, output_value):
        errors = []
        assert uut.parse(errors, loc, input_value) == output_value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ",
        [
            set,
            MutableSet,
        ],
    )
    def test_parse_returns_different_set_than_the_input_one(self, uut: UUT):
        errors = []
        input_mapping = {1, 3.14, "spam"}
        output_mapping = uut.parse(errors, loc, input_mapping)
        assert input_mapping == output_mapping
        assert input_mapping is not output_mapping
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, input_value, expected_errors",
        [
            (set, 1, [ErrorFactory.invalid_type(loc, 1, [set], [Set, Sequence], [str, bytes])]),
            (set[Any], 1, [ErrorFactory.invalid_type(loc, 1, [set[Any]], [Set, Sequence], [str, bytes])]),
            (MutableSet, 1, [ErrorFactory.invalid_type(loc, 1, [MutableSet], [Set, Sequence], [str, bytes])]),
            (MutableSet[Any], 1, [ErrorFactory.invalid_type(loc, 1, [MutableSet[Any]], [Set, Sequence], [str, bytes])]),
        ],
    )
    def test_parse_fails_if_invalid_input_given(self, uut: UUT, input_value, expected_errors):
        errors = []
        assert uut.parse(errors, loc, input_value) == Unset
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ, input_value, expected_errors",
        [
            (set, [[1]], [ErrorFactory.conversion_error(loc, [[1]], set, "some elements are unhashable")]),
            (set[Any], [[1]], [ErrorFactory.conversion_error(loc, [[1]], set[Any], "some elements are unhashable")]),
            (
                MutableSet[Any],
                [[1]],
                [ErrorFactory.conversion_error(loc, [[1]], MutableSet[Any], "some elements are unhashable")],
            ),
        ],
    )
    def test_parse_fails_if_one_or_more_items_are_unhashable(self, uut: UUT, input_value, expected_errors):
        errors = []
        assert uut.parse(errors, loc, input_value) == Unset
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ",
        [set, set[Any], Set, MutableSet[Any]],
    )
    def test_accept(self, uut: UUT, visitor_mock):
        value = {1, 3.14, "spam"}
        visitor_mock.visit_set_begin.expect_call(loc, value)
        visitor_mock.visit_any.expect_call(loc + Loc.irrelevant(), 1)
        visitor_mock.visit_any.expect_call(loc + Loc.irrelevant(), 3.14)
        visitor_mock.visit_any.expect_call(loc + Loc.irrelevant(), "spam")
        visitor_mock.visit_set_end.expect_call(loc, value)
        uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ",
        [set, set[Any], Set, MutableSet[Any]],
    )
    def test_accept_with_skip(self, uut: UUT, visitor_mock):
        value = {1, 3.14, "spam"}
        visitor_mock.visit_set_begin.expect_call(loc, value).will_once(Return(True))
        uut.accept(visitor_mock, loc, value)


class TestTypedMutableSetTypeHandler:
    UUT = TypeHandler

    @pytest.fixture
    def uut(self, typ, type_handler_factory_mock, type_handler_mock):
        for arg in get_args(typ):
            type_handler_factory_mock.expect_call(arg).will_once(
                Return(getattr(type_handler_mock, f"{arg.__name__}_handler"))
            )
        return TypedMutableSetTypeHandler(typ, type_handler_factory_mock)

    @pytest.mark.parametrize(
        "typ, expected_error",
        [
            (int, "unsupported type; got <class 'int'>, expected MutableSet"),
            (dict[str, int], "unsupported type; got dict[str, int], expected MutableSet"),
            (set, "unsupported type; got <class 'set'>, expected MutableSet[T]"),
            (MutableSet, "unsupported type; got typing.MutableSet, expected MutableSet[T]"),
        ],
    )
    def test_constructing_fails_for_unsupported_type(self, typ, expected_error, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            TypedMutableSetTypeHandler(typ, type_handler_factory_mock)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (set[int], {"foo": 1}),
        ],
    )
    def test_construct_with_type_opts(self, typ, type_handler_factory_mock, type_opts, type_handler_mock):
        for arg in get_args(typ):
            type_handler_factory_mock.expect_call(arg, **type_opts).will_once(Return(type_handler_mock))
        TypedMutableSetTypeHandler(typ, type_handler_factory_mock, **type_opts)

    @pytest.mark.parametrize(
        "typ",
        [
            set[int],
            MutableSet[int],
        ],
    )
    def test_parse_successfully(self, uut: UUT, type_handler_mock):
        errors = []
        type_handler_mock.int_handler.parse.expect_call(errors, loc + Loc.irrelevant(), "1").will_once(Return(1))
        assert uut.parse(errors, loc, {"1"}) == {1}
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ",
        [
            set[int],
            MutableSet[int],
        ],
    )
    def test_successful_parse_returns_mutable_mapping_proxy(self, uut: UUT, type_handler_mock):
        errors = []
        type_handler_mock.int_handler.parse.expect_call(errors, Loc.irrelevant(), "1").will_once(Return(1))
        m = uut.parse(errors, loc, [])
        assert len(errors) == 0
        assert isinstance(m, MutableSet)
        m.add("1")
        assert m == {1}

    @pytest.mark.parametrize(
        "typ, input_value, expected_errors",
        [
            (set[int], 1, [ErrorFactory.invalid_type(loc, 1, [set[int]], [Set, Sequence], [str, bytes])]),
            (MutableSet[int], 1, [ErrorFactory.invalid_type(loc, 1, [MutableSet[int]], [Set, Sequence], [str, bytes])]),
        ],
    )
    def test_parse_fails_if_invalid_input_given(self, uut: UUT, input_value, expected_errors):
        errors = []
        assert uut.parse(errors, loc, input_value) == Unset
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ",
        [
            set[int],
            MutableSet[int],
        ],
    )
    def test_parse_fails_if_item_parsing_fails(self, uut: UUT, type_handler_mock):
        def parse(errors: list[Error], loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, int))
            return Unset

        errors = []
        type_handler_mock.int_handler.parse.expect_call(errors, loc + Loc.irrelevant(), "spam").will_once(Invoke(parse))
        assert uut.parse(errors, loc, ["spam"]) == Unset
        assert errors == [
            ErrorFactory.parse_error(loc + Loc.irrelevant(), "spam", int),
        ]

    @pytest.mark.parametrize(
        "typ",
        [
            set[int],
            MutableSet[int],
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, type_handler_mock):
        value = {1, 2}
        visitor_mock.visit_set_begin.expect_call(loc, value)
        type_handler_mock.int_handler.accept.expect_call(visitor_mock, loc + Loc.irrelevant(), 1)
        type_handler_mock.int_handler.accept.expect_call(visitor_mock, loc + Loc.irrelevant(), 2)
        visitor_mock.visit_set_end.expect_call(loc, value)
        uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ",
        [
            set[int],
            MutableSet[int],
        ],
    )
    def test_accept_with_skip(self, uut: UUT, visitor_mock, type_handler_mock):
        value = {1, 2}
        visitor_mock.visit_set_begin.expect_call(loc, value).will_once(Return(True))
        uut.accept(visitor_mock, loc, value)
