from typing import Any, Mapping, MutableMapping, get_args

import pytest

from mockify.api import Return, Invoke

from modelity._parsing.type_handlers.mapping import AnyMutableMappingTypeHandler, TypedMutableMappingTypeHandler
from modelity.base import TypeHandler
from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset

from .common import loc


class TestAnyMutableMappingTypeHandler:
    UUT = TypeHandler

    @pytest.fixture
    def uut(self, typ):
        return AnyMutableMappingTypeHandler(typ)

    @pytest.mark.parametrize(
        "typ, expected_error",
        [
            (int, "unsupported type; got <class 'int'>, expected MutableMapping"),
            (list[int], "unsupported type; got list[int], expected MutableMapping"),
            (
                dict[str, int],
                "unsupported type; got dict[str, int], expected one of: MutableMapping, MutableMapping[Any, Any]",
            ),
            (
                MutableMapping[str, int],
                "unsupported type; got typing.MutableMapping[str, int], expected one of: MutableMapping, MutableMapping[Any, Any]",
            ),
        ],
    )
    def test_construct_fails_if_unsupported_type_given(self, typ, expected_error):
        with pytest.raises(TypeError) as excinfo:
            AnyMutableMappingTypeHandler(typ)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "typ, input_value, output_value",
        [
            (dict, {}, {}),
            (dict, {"a": 1, "b": "spam"}, {"a": 1, "b": "spam"}),
            (dict[Any, Any], {"a": 1, "b": "spam"}, {"a": 1, "b": "spam"}),
            (MutableMapping, {"a": 1, "b": "spam"}, {"a": 1, "b": "spam"}),
            (MutableMapping[Any, Any], {"a": 1, "b": "spam"}, {"a": 1, "b": "spam"}),
        ],
    )
    def test_parse_successfully(self, uut: UUT, input_value, output_value):
        errors = []
        assert uut.parse(errors, loc, input_value) == output_value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ",
        [
            dict,
        ],
    )
    def test_parse_returns_different_mapping_than_the_input_one(self, uut: UUT):
        errors = []
        input_mapping = {"one": 1}
        output_mapping = uut.parse(errors, loc, input_mapping)
        assert input_mapping == output_mapping
        assert input_mapping is not output_mapping
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, input_value, expected_errors",
        [
            (dict, 1, [ErrorFactory.invalid_type(loc, 1, [dict], [Mapping])]),
            (MutableMapping, 1, [ErrorFactory.invalid_type(loc, 1, [MutableMapping], [Mapping])]),
        ],
    )
    def test_parse_fails_if_non_mapping_given(self, uut: UUT, input_value, expected_errors):
        errors = []
        assert uut.parse(errors, loc, input_value) == Unset
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ",
        [
            dict,
            MutableMapping,
            dict[Any, Any],
            MutableMapping[Any, Any],
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock):
        visitor_mock.visit_mapping_begin.expect_call(loc, {"one": 1, "two": 2})
        visitor_mock.visit_any.expect_call(loc + Loc("one"), 1)
        visitor_mock.visit_any.expect_call(loc + Loc("two"), 2)
        visitor_mock.visit_mapping_end.expect_call(loc, {"one": 1, "two": 2})
        uut.accept(visitor_mock, loc, {"one": 1, "two": 2})

    @pytest.mark.parametrize(
        "typ",
        [
            dict,
            MutableMapping,
            dict[Any, Any],
            MutableMapping[Any, Any],
        ],
    )
    def test_accept_with_skip(self, uut: UUT, visitor_mock):
        visitor_mock.visit_mapping_begin.expect_call(loc, {"one": 1, "two": 2}).will_once(Return(True))
        uut.accept(visitor_mock, loc, {"one": 1, "two": 2})


class TestTypedMutableMappingTypeHandler:
    UUT = TypeHandler

    @pytest.fixture
    def uut(self, typ, type_handler_factory_mock, type_handler_mock):
        for arg in get_args(typ):
            type_handler_factory_mock.expect_call(arg).will_once(
                Return(getattr(type_handler_mock, f"{arg.__name__}_handler"))
            )
        return TypedMutableMappingTypeHandler(typ, type_handler_factory_mock)

    @pytest.mark.parametrize(
        "typ, expected_error",
        [
            (int, "unsupported type; got <class 'int'>, expected MutableMapping"),
            (dict, "unsupported type; got <class 'dict'>, expected MutableMapping[K, V]"),
            (MutableMapping, "unsupported type; got typing.MutableMapping, expected MutableMapping[K, V]"),
        ],
    )
    def test_construct_fails_if_unsupported_type_given(self, typ, expected_error, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            TypedMutableMappingTypeHandler(typ, type_handler_factory_mock)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (dict[str, int], {"foo": 1}),
        ],
    )
    def test_construct_with_type_opts(self, typ, type_handler_factory_mock, type_opts, type_handler_mock):
        for arg in get_args(typ):
            type_handler_factory_mock.expect_call(arg, **type_opts).will_once(Return(type_handler_mock))
        TypedMutableMappingTypeHandler(typ, type_handler_factory_mock, **type_opts)

    @pytest.mark.parametrize(
        "typ",
        [
            dict[str, int],
            MutableMapping[str, int],
        ],
    )
    def test_parse_successfully(self, uut: UUT, type_handler_mock):
        errors = []
        type_handler_mock.str_handler.parse.expect_call(errors, loc + Loc.irrelevant(), "one").will_once(Return("one"))
        type_handler_mock.int_handler.parse.expect_call(errors, loc + Loc("one"), "1").will_once(Return(1))
        assert uut.parse(errors, loc, {"one": "1"}) == {"one": 1}
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ",
        [
            dict[str, int],
            MutableMapping[str, int],
        ],
    )
    def test_successful_parse_returns_mutable_mapping_proxy(self, uut: UUT, type_handler_mock):
        errors = []
        type_handler_mock.str_handler.parse.expect_call(errors, Loc.irrelevant(), "one").will_once(Return("one"))
        type_handler_mock.int_handler.parse.expect_call(errors, Loc("one"), "1").will_once(Return(1))
        m = uut.parse(errors, loc, {})
        assert len(errors) == 0
        assert isinstance(m, MutableMapping)
        m["one"] = "1"
        assert m == {"one": 1}

    @pytest.mark.parametrize(
        "typ, input_value, expected_errors",
        [
            (dict[Any, Any], 1, [ErrorFactory.invalid_type(loc, 1, [dict[Any, Any]], [Mapping])]),
            (dict[str, int], 1, [ErrorFactory.invalid_type(loc, 1, [dict[str, int]], [Mapping])]),
        ],
    )
    def test_parse_fails_if_non_mapping_given(self, uut: UUT, input_value, expected_errors):
        errors = []
        assert uut.parse(errors, loc, input_value) == Unset
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ",
        [
            dict[str, int],
        ],
    )
    def test_when_key_parsing_fails_then_value_parsing_is_skipped(self, uut: UUT, type_handler_mock):
        def parse(errors: list[Error], loc: Loc, value: Any):
            errors.append(ErrorFactory.invalid_type(loc, value, [str]))
            return Unset

        errors = []
        type_handler_mock.str_handler.parse.expect_call(errors, loc + Loc.irrelevant(), 1).will_once(Invoke(parse))
        assert uut.parse(errors, loc, {1: "one"}) == Unset
        assert errors == [ErrorFactory.invalid_type(loc + Loc.irrelevant(), 1, [str])]

    @pytest.mark.parametrize(
        "typ",
        [
            dict[str, int],
            MutableMapping[str, int],
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, type_handler_mock):
        value = {"one": 1, "two": 2}
        visitor_mock.visit_mapping_begin.expect_call(loc, value)
        type_handler_mock.int_handler.accept.expect_call(visitor_mock, loc + Loc("one"), value["one"])
        type_handler_mock.int_handler.accept.expect_call(visitor_mock, loc + Loc("two"), value["two"])
        visitor_mock.visit_mapping_end.expect_call(loc, value)
        uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ",
        [
            dict[str, int],
            MutableMapping[str, int],
        ],
    )
    def test_accept_with_skip(self, uut: UUT, visitor_mock):
        value = {"one": 1, "two": 2}
        visitor_mock.visit_mapping_begin.expect_call(loc, value).will_once(Return(True))
        uut.accept(visitor_mock, loc, value)
