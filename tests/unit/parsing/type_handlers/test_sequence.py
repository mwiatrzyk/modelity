from typing import Any, MutableSequence, Sequence, get_args

import pytest

from mockify.api import Return, Invoke

from modelity._parsing.type_handlers.sequence import (
    AnyMutableSequenceHandler,
    AnySequenceTypeHandler,
    FixedTupleTypeHandler,
    TypedMutableSequenceHandler,
    TypedSequenceTypeHandler,
)
from modelity.base import TypeHandler
from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset

from .common import loc


class TestAnyMutableSequenceHandler:
    UUT = TypeHandler

    @pytest.fixture
    def uut(self, typ):
        return AnyMutableSequenceHandler(typ)

    @pytest.mark.parametrize(
        "typ, expected_error",
        [
            (int, "unsupported type; got <class 'int'>, expected MutableSequence"),
            (dict[str, int], "unsupported type; got dict[str, int], expected MutableSequence"),
            (list[int], "unsupported type; got list[int], expected one of: MutableSequence, MutableSequence[Any]"),
        ],
    )
    def test_constructing_fails_for_unsupported_type(self, typ, expected_error):
        with pytest.raises(TypeError) as excinfo:
            AnyMutableSequenceHandler(typ)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "typ, input_value, output_value",
        [
            (list, [], []),
            (list, [1, 3.14, "spam"], [1, 3.14, "spam"]),
            (list[Any], [], []),
            (list[Any], [1, 3.14, "spam"], [1, 3.14, "spam"]),
            (MutableSequence[Any], [], []),
            (MutableSequence[Any], [1, 3.14, "spam"], [1, 3.14, "spam"]),
        ],
    )
    def test_parse_successfully(self, uut: UUT, input_value, output_value):
        errors = []
        assert uut.parse(errors, loc, input_value) == output_value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ",
        [
            list,
        ],
    )
    def test_parse_returns_different_sequence_than_the_input_one(self, uut: UUT):
        errors = []
        input_mapping = [1, 3.14, "spam"]
        output_mapping = uut.parse(errors, loc, input_mapping)
        assert input_mapping == output_mapping
        assert input_mapping is not output_mapping
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, input_value, expected_errors",
        [
            (list, 1, [ErrorFactory.invalid_type(loc, 1, [list], [Sequence], [str, bytes])]),
            (list[Any], 1, [ErrorFactory.invalid_type(loc, 1, [list[Any]], [Sequence], [str, bytes])]),
            (MutableSequence, 1, [ErrorFactory.invalid_type(loc, 1, [MutableSequence], [Sequence], [str, bytes])]),
            (
                MutableSequence[Any],
                1,
                [ErrorFactory.invalid_type(loc, 1, [MutableSequence[Any]], [Sequence], [str, bytes])],
            ),
        ],
    )
    def test_parse_fails_if_invalid_input_given(self, uut: UUT, input_value, expected_errors):
        errors = []
        assert uut.parse(errors, loc, input_value) == Unset
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ",
        [list, list[Any], MutableSequence, MutableSequence[Any]],
    )
    def test_accept(self, uut: UUT, visitor_mock):
        value = [1, 3.14, "spam"]
        visitor_mock.visit_sequence_begin.expect_call(loc, value)
        visitor_mock.visit_any.expect_call(loc + Loc(0), value[0])
        visitor_mock.visit_any.expect_call(loc + Loc(1), value[1])
        visitor_mock.visit_any.expect_call(loc + Loc(2), value[2])
        visitor_mock.visit_sequence_end.expect_call(loc, value)
        uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ",
        [list, list[Any], MutableSequence, MutableSequence[Any]],
    )
    def test_accept_with_skip(self, uut: UUT, visitor_mock):
        value = [1, 3.14, "spam"]
        visitor_mock.visit_sequence_begin.expect_call(loc, value).will_once(Return(True))
        uut.accept(visitor_mock, loc, value)


class TestTypedMutableSequenceHandler:
    UUT = TypeHandler

    @pytest.fixture
    def uut(self, typ, type_handler_factory_mock, type_handler_mock):
        for arg in get_args(typ):
            type_handler_factory_mock.expect_call(arg).will_once(
                Return(getattr(type_handler_mock, f"{arg.__name__}_handler"))
            )
        return TypedMutableSequenceHandler(typ, type_handler_factory_mock)

    @pytest.mark.parametrize(
        "typ, expected_error",
        [
            (int, "unsupported type; got <class 'int'>, expected MutableSequence"),
            (dict[str, int], "unsupported type; got dict[str, int], expected MutableSequence"),
            (list, "unsupported type; got <class 'list'>, expected MutableSequence[T]"),
        ],
    )
    def test_constructing_fails_for_unsupported_type(self, typ, expected_error, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            TypedMutableSequenceHandler(typ, type_handler_factory_mock)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (list[int], {"foo": 1}),
        ],
    )
    def test_construct_with_type_opts(self, typ, type_handler_factory_mock, type_opts, type_handler_mock):
        for arg in get_args(typ):
            type_handler_factory_mock.expect_call(arg, **type_opts).will_once(Return(type_handler_mock))
        TypedMutableSequenceHandler(typ, type_handler_factory_mock, **type_opts)

    @pytest.mark.parametrize(
        "typ",
        [
            list[int],
            MutableSequence[int],
        ],
    )
    def test_parse_successfully(self, uut: UUT, type_handler_mock):
        errors = []
        type_handler_mock.int_handler.parse.expect_call(errors, loc + Loc(0), "1").will_once(Return(1))
        assert uut.parse(errors, loc, ["1"]) == [1]
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ",
        [
            list[int],
            MutableSequence[int],
        ],
    )
    def test_successful_parse_returns_mutable_mapping_proxy(self, uut: UUT, type_handler_mock):
        errors = []
        type_handler_mock.int_handler.parse.expect_call(errors, Loc(0), "1").will_once(Return(1))
        m = uut.parse(errors, loc, [])
        assert len(errors) == 0
        assert isinstance(m, MutableSequence)
        m.append("1")
        assert m == [1]

    @pytest.mark.parametrize(
        "typ, input_value, expected_errors",
        [
            (list[int], 1, [ErrorFactory.invalid_type(loc, 1, [list[int]], [Sequence], [str, bytes])]),
            (
                MutableSequence[Any],
                1,
                [ErrorFactory.invalid_type(loc, 1, [MutableSequence[Any]], [Sequence], [str, bytes])],
            ),
        ],
    )
    def test_parse_fails_if_invalid_input_given(self, uut: UUT, input_value, expected_errors):
        errors = []
        assert uut.parse(errors, loc, input_value) == Unset
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ",
        [
            list[int],
            MutableSequence[int],
        ],
    )
    def test_parse_fails_if_item_parsing_fails(self, uut: UUT, type_handler_mock):
        def parse(errors: list[Error], loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, int))
            return Unset

        errors = []
        type_handler_mock.int_handler.parse.expect_call(errors, loc + Loc(0), "spam").will_once(Invoke(parse))
        assert uut.parse(errors, loc, ["spam"]) == Unset
        assert errors == [
            ErrorFactory.parse_error(loc + Loc(0), "spam", int),
        ]

    @pytest.mark.parametrize(
        "typ",
        [
            list[int],
            MutableSequence[int],
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, type_handler_mock):
        value = [1, 2]
        visitor_mock.visit_sequence_begin.expect_call(loc, value)
        type_handler_mock.int_handler.accept.expect_call(visitor_mock, loc + Loc(0), value[0])
        type_handler_mock.int_handler.accept.expect_call(visitor_mock, loc + Loc(1), value[1])
        visitor_mock.visit_sequence_end.expect_call(loc, value)
        uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ",
        [
            list[int],
            MutableSequence[int],
        ],
    )
    def test_accept_with_skip(self, uut: UUT, visitor_mock):
        value = [1, 2]
        visitor_mock.visit_sequence_begin.expect_call(loc, value).will_once(Return(True))
        uut.accept(visitor_mock, loc, value)


class TestAnySequenceTypeHandler:
    UUT = TypeHandler

    @pytest.fixture
    def uut(self, typ):
        return AnySequenceTypeHandler(typ)

    @pytest.mark.parametrize(
        "typ, expected_error",
        [
            (int, "unsupported type; got <class 'int'>, expected Sequence"),
            (dict[str, int], "unsupported type; got dict[str, int], expected Sequence"),
            (
                tuple[int, ...],
                "unsupported type; got tuple[int, ...], expected one of: Sequence, Sequence[Any], tuple[Any, ...]",
            ),
        ],
    )
    def test_constructing_fails_for_unsupported_type(self, typ, expected_error, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            AnySequenceTypeHandler(typ)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "typ, input_value, output_value",
        [
            (tuple, [], tuple()),
            (tuple, [1, 3.14, "spam"], (1, 3.14, "spam")),
            (tuple[Any, ...], [1, 3.14, "spam"], (1, 3.14, "spam")),
        ],
    )
    def test_parse_successfully(self, uut: UUT, input_value, output_value):
        errors = []
        assert uut.parse(errors, loc, input_value) == output_value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, input_value, expected_errors",
        [
            (tuple, 1, [ErrorFactory.invalid_type(loc, 1, [tuple], [Sequence], [str, bytes])]),
            (tuple[Any, ...], 1, [ErrorFactory.invalid_type(loc, 1, [tuple[Any, ...]], [Sequence], [str, bytes])]),
        ],
    )
    def test_parse_fails_if_invalid_input_given(self, uut: UUT, input_value, expected_errors):
        errors = []
        assert uut.parse(errors, loc, input_value) == Unset
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ",
        [
            tuple,
            tuple[Any, ...],
            Sequence,
            Sequence[Any],
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock):
        value = [1, 3.14, "spam"]
        visitor_mock.visit_sequence_begin.expect_call(loc, value)
        visitor_mock.visit_any.expect_call(loc + Loc(0), value[0])
        visitor_mock.visit_any.expect_call(loc + Loc(1), value[1])
        visitor_mock.visit_any.expect_call(loc + Loc(2), value[2])
        visitor_mock.visit_sequence_end.expect_call(loc, value)
        uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ",
        [tuple, tuple[Any, ...], Sequence, Sequence[Any]],
    )
    def test_accept_with_skip(self, uut: UUT, visitor_mock):
        value = [1, 3.14, "spam"]
        visitor_mock.visit_sequence_begin.expect_call(loc, value).will_once(Return(True))
        uut.accept(visitor_mock, loc, value)


class TestTypedSequenceTypeHandler:
    UUT = TypeHandler

    @pytest.fixture
    def uut(self, typ, type_handler_factory_mock, type_handler_mock):
        arg = get_args(typ)[0]
        type_handler_factory_mock.expect_call(arg).will_once(
            Return(getattr(type_handler_mock, f"{arg.__name__}_handler"))
        )
        return TypedSequenceTypeHandler(typ, type_handler_factory_mock)

    @pytest.mark.parametrize(
        "typ, expected_error",
        [
            (int, "unsupported type; got <class 'int'>, expected Sequence"),
            (dict[str, int], "unsupported type; got dict[str, int], expected Sequence"),
            (
                tuple[str, int, float],
                "unsupported type; got tuple[str, int, float], expected one of: Sequence[T], tuple[T, ...]",
            ),
            (tuple, "unsupported type; got <class 'tuple'>, expected one of: Sequence[T], tuple[T, ...]"),
        ],
    )
    def test_constructing_fails_for_unsupported_type(self, typ, expected_error, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            TypedSequenceTypeHandler(typ, type_handler_factory_mock)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (tuple[int, ...], {"foo": 1}),
            (Sequence[int], {"foo": 1, "bar": 2}),
        ],
    )
    def test_construct_with_type_opts(self, typ, type_handler_factory_mock, type_opts, type_handler_mock):
        for arg in [x for x in get_args(typ) if x is not Ellipsis]:
            type_handler_factory_mock.expect_call(arg, **type_opts).will_once(Return(type_handler_mock))
        TypedSequenceTypeHandler(typ, type_handler_factory_mock, **type_opts)

    @pytest.mark.parametrize(
        "typ",
        [
            tuple[int, ...],
            Sequence[int],
        ],
    )
    def test_parse_successfully(self, uut: UUT, type_handler_mock):
        errors = []
        type_handler_mock.int_handler.parse.expect_call(errors, loc + Loc(0), "1").will_once(Return(1))
        assert uut.parse(errors, loc, ["1"]) == (1,)
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, input_value, expected_errors",
        [
            (tuple[int, ...], 1, [ErrorFactory.invalid_type(loc, 1, [tuple[int, ...]], [Sequence], [str, bytes])]),
            (Sequence[int], 1, [ErrorFactory.invalid_type(loc, 1, [Sequence[int]], [Sequence], [str, bytes])]),
        ],
    )
    def test_parse_fails_if_invalid_input_given(self, uut: UUT, input_value, expected_errors):
        errors = []
        assert uut.parse(errors, loc, input_value) == Unset
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ",
        [
            tuple[int, ...],
            Sequence[int],
        ],
    )
    def test_parse_fails_if_item_parsing_fails(self, uut: UUT, type_handler_mock):
        def parse(errors: list[Error], loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, int))
            return Unset

        errors = []
        type_handler_mock.int_handler.parse.expect_call(errors, loc + Loc(0), "spam").will_once(Invoke(parse))
        assert uut.parse(errors, loc, ["spam"]) == Unset
        assert errors == [
            ErrorFactory.parse_error(loc + Loc(0), "spam", int),
        ]

    @pytest.mark.parametrize(
        "typ",
        [
            tuple[int, ...],
            Sequence[int],
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, type_handler_mock):
        value = [1, 2]
        visitor_mock.visit_sequence_begin.expect_call(loc, value)
        type_handler_mock.int_handler.accept.expect_call(visitor_mock, loc + Loc(0), value[0])
        type_handler_mock.int_handler.accept.expect_call(visitor_mock, loc + Loc(1), value[1])
        visitor_mock.visit_sequence_end.expect_call(loc, value)
        uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ",
        [
            tuple[int, ...],
            Sequence[int],
        ],
    )
    def test_accept_with_skip(self, uut: UUT, visitor_mock):
        value = [1, 2]
        visitor_mock.visit_sequence_begin.expect_call(loc, value).will_once(Return(True))
        uut.accept(visitor_mock, loc, value)


class TestFixedTupleTypeHandler:
    UUT = TypeHandler

    @pytest.fixture
    def uut(self, typ, type_handler_factory_mock, type_handler_mock):
        for arg in get_args(typ):
            type_handler_factory_mock.expect_call(arg).will_once(
                Return(getattr(type_handler_mock, f"{arg.__name__}_handler"))
            )
        return FixedTupleTypeHandler(typ, type_handler_factory_mock)

    @pytest.mark.parametrize(
        "typ, expected_error",
        [
            (int, "unsupported type; got <class 'int'>, expected tuple[A, B, ..., Z]"),
            (dict[str, int], "unsupported type; got dict[str, int], expected tuple[A, B, ..., Z]"),
            (tuple, "unsupported type; got <class 'tuple'>, expected tuple[A, B, ..., Z]"),
            (tuple[int, ...], "unsupported type; got tuple[int, ...], expected tuple[A, B, ..., Z]"),
            (Sequence, "unsupported type; got typing.Sequence, expected tuple[A, B, ..., Z]"),
            (Sequence[int], "unsupported type; got typing.Sequence[int], expected tuple[A, B, ..., Z]"),
        ],
    )
    def test_constructing_fails_for_unsupported_type(self, typ, expected_error, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            FixedTupleTypeHandler(typ, type_handler_factory_mock)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (tuple[int], {"foo": 1}),
            (tuple[int, float], {"foo": 2}),
            (tuple[int, float, int, float, str], {"foo": 3}),
        ],
    )
    def test_construct_with_type_opts(self, typ, type_handler_factory_mock, type_opts, type_handler_mock):
        for arg in get_args(typ):
            type_handler_factory_mock.expect_call(arg, **type_opts).will_once(Return(type_handler_mock))
        FixedTupleTypeHandler(typ, type_handler_factory_mock, **type_opts)

    @pytest.mark.parametrize(
        "typ",
        [
            tuple[int, float, str],
        ],
    )
    def test_parse_successfully(self, uut: UUT, type_handler_mock):
        errors = []
        type_handler_mock.int_handler.parse.expect_call(errors, loc + Loc(0), "1").will_once(Return(1))
        type_handler_mock.float_handler.parse.expect_call(errors, loc + Loc(1), "3.14").will_once(Return(3.14))
        type_handler_mock.str_handler.parse.expect_call(errors, loc + Loc(2), "spam").will_once(Return("spam"))
        assert uut.parse(errors, loc, ["1", "3.14", "spam"]) == (1, 3.14, "spam")
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, input_value, expected_errors",
        [
            (tuple[int, float], 1, [ErrorFactory.invalid_type(loc, 1, [tuple[int, float]], [Sequence], [str, bytes])]),
            (tuple[int, float], [1], [ErrorFactory.invalid_tuple_length(loc, (1,), (int, float))]),
        ],
    )
    def test_parse_fails_if_invalid_input_given(self, uut: UUT, input_value, expected_errors):
        errors = []
        assert uut.parse(errors, loc, input_value) == Unset
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ",
        [
            tuple[int, float],
        ],
    )
    def test_parse_fails_if_item_parsing_fails(self, uut: UUT, type_handler_mock):
        def parse(typ: type, errors: list[Error], loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, typ))
            return Unset

        errors = []
        type_handler_mock.int_handler.parse.expect_call(errors, loc + Loc(0), "foo").will_once(Invoke(parse, int))
        type_handler_mock.float_handler.parse.expect_call(errors, loc + Loc(1), "bar").will_once(Invoke(parse, float))
        assert uut.parse(errors, loc, ["foo", "bar"]) == Unset
        assert errors == [
            ErrorFactory.parse_error(loc + Loc(0), "foo", int),
            ErrorFactory.parse_error(loc + Loc(1), "bar", float),
        ]

    @pytest.mark.parametrize(
        "typ",
        [
            tuple[int, float],
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, type_handler_mock):
        value = (1, 3.14)
        visitor_mock.visit_sequence_begin.expect_call(loc, value)
        type_handler_mock.int_handler.accept.expect_call(visitor_mock, loc + Loc(0), value[0])
        type_handler_mock.float_handler.accept.expect_call(visitor_mock, loc + Loc(1), value[1])
        visitor_mock.visit_sequence_end.expect_call(loc, value)
        uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ",
        [
            tuple[int, float],
        ],
    )
    def test_accept_with_skip(self, uut: UUT, visitor_mock):
        value = (1, 3.14)
        visitor_mock.visit_sequence_begin.expect_call(loc, value).will_once(Return(True))
        uut.accept(visitor_mock, loc, value)
