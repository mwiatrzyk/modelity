from typing import Annotated, Any, Optional, Sequence, Union, get_args

import pytest

from mockify.api import Return, Mock, Invoke, ordered, satisfied, _

from modelity import _utils
from modelity._parsing.type_handlers.special import (
    AnnotatedTypeHandler,
    DeferredTypeHandler,
    OptionalTypeHandler,
    LooseOptionalTypeHandler,
    StrictOptionalTypeHandler,
    UnionTypeHandler,
)
from modelity.base import TypeHandlerWithValidation, Constraint, ModelVisitor, TypeHandler
from modelity.constraints import Ge
from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.typing import Deferred, LooseOptional, StrictOptional
from modelity.unset import Unset, UnsetType

from .common import loc


class MockConstraint(Constraint):

    def __init__(self, name: str):
        self.mock = Mock(name)

    def __repr__(self) -> str:
        return f"MockConstraint({self.mock!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any) -> bool:
        return self.mock.validate(errors, loc, value)  # type: ignore


class TestAnnotatedTypeHandler:
    UUT = TypeHandlerWithValidation

    @pytest.fixture
    def wrapped_type(self, typ):
        args = get_args(typ)
        assert len(args) > 1
        return args[0]

    @pytest.fixture
    def wrapped_constraints(self, typ):
        args = get_args(typ)
        assert len(args) > 1
        return args[1:]

    @pytest.fixture
    def wrapped_type_handler(self, wrapped_type):
        mock = Mock(f"{wrapped_type.__name__}_type_handler")
        with satisfied(mock):
            yield mock

    @pytest.fixture
    def uut(self, typ, type_opts, wrapped_type, type_handler_factory_mock, wrapped_type_handler):
        type_handler_factory_mock.expect_call(wrapped_type, **type_opts).will_once(Return(wrapped_type_handler))
        return AnnotatedTypeHandler(typ, type_handler_factory_mock, **type_opts)

    def test_construct_fails_if_not_annotated(self, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            AnnotatedTypeHandler(object, type_handler_factory_mock)
        assert str(excinfo.value) == "expected Annotated[T, ...], got <class 'object'> instead"

    def test_construct_fails_if_annotated_with_invalid_constraints(self, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            AnnotatedTypeHandler(Annotated[int, 1, 2, "spam"], type_handler_factory_mock)
        assert str(excinfo.value) == "expected Constraint, got 1 instead"

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (Annotated[int, MockConstraint("one")], {}),
            (Annotated[int, MockConstraint("two")], {"foo": 1, "bar": 2}),
        ],
    )
    def test_parse_successfully(self, uut: UUT, wrapped_type_handler, wrapped_constraints):
        errors = []
        wrapped_type_handler.parse.expect_call(errors, loc, 123).will_once(Return(123))
        for c in wrapped_constraints:
            c.mock.validate.expect_call(errors, loc, 123).will_once(Return(True))
        assert uut.parse(errors, loc, 123) == 123

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (Annotated[int, MockConstraint("one")], {}),
        ],
    )
    def test_parse_fails_if_type_handler_fails(self, uut: UUT, wrapped_type_handler):
        def parse(errors: list[Error], loc: Loc, value: Any):
            errors.append(ErrorFactory.parse_error(loc, value, int))
            return Unset

        errors = []
        wrapped_type_handler.parse.expect_call(_, loc, "invalid").will_once(Invoke(parse))
        assert uut.parse(errors, loc, "invalid") == Unset
        assert errors == [ErrorFactory.parse_error(loc, "invalid", int)]

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (Annotated[int, MockConstraint("one")], {}),
        ],
    )
    def test_parse_fails_if_validation_fails(self, uut: UUT, wrapped_type_handler, wrapped_constraints):
        def validate(errors: list[Error], loc: Loc, value: Any):
            errors.append(ErrorFactory.out_of_range(loc, value, min_inclusive=0))
            return Unset

        errors = []
        wrapped_type_handler.parse.expect_call(_, loc, -1).will_once(Return(-1))
        for c in wrapped_constraints:
            c.mock.validate.expect_call(errors, loc, -1).will_once(Invoke(validate))
        assert uut.parse(errors, loc, -1) == Unset
        assert errors == [ErrorFactory.out_of_range(loc, -1, min_inclusive=0)]

    @pytest.mark.parametrize(
        "typ, type_opts, value",
        [
            (Annotated[int, MockConstraint("one")], {}, 123),
            (Annotated[int, MockConstraint("two")], {"foo": 1, "bar": 2}, 456),
        ],
    )
    def test_accept_forwards_call_to_wrapped_type_handler(self, uut: UUT, visitor_mock, value, wrapped_type_handler):
        wrapped_type_handler.accept.expect_call(visitor_mock, loc, value)
        uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ, type_opts, value",
        [
            (Annotated[int, MockConstraint("one"), MockConstraint("two"), MockConstraint("three")], {}, 123),
        ],
    )
    def test_validate_triggers_all_defined_constraints(self, uut: UUT, value, wrapped_constraints: Sequence):
        errors = []
        for c in wrapped_constraints:
            c.mock.validate.expect_call(errors, loc, value).will_once(Return(True))
        uut.validate(errors, loc, value)

    @pytest.mark.parametrize(
        "typ, type_opts, value",
        [
            (Annotated[int, MockConstraint("one"), MockConstraint("two"), MockConstraint("three")], {}, 123),
        ],
    )
    def test_validate_terminates_after_first_false(self, uut: UUT, value, wrapped_constraints: Sequence):
        errors = []
        wrapped_constraints[0].mock.validate.expect_call(errors, loc, value).will_once(Return(False))
        uut.validate(errors, loc, value)


class TestDeferredTypeHandler:
    UUT = DeferredTypeHandler

    @pytest.fixture
    def uut(self, typ, type_handler_factory_mock, type_handler_mock):
        args = get_args(typ)
        types = get_args(args[0])[:-1]
        names = "_".join(x.__name__ for x in types)
        wrapped_type = types[0] if len(types) == 1 else _utils.make_union_type(types)
        type_handler_factory_mock.expect_call(wrapped_type).will_once(
            Return(getattr(type_handler_mock, f"{names}_handler"))
        )
        return DeferredTypeHandler(typ, type_handler_factory_mock)

    @pytest.mark.parametrize(
        "typ, expected_error",
        [
            (object, "expected Deferred[T], got <class 'object'> instead"),
            (Deferred[UnsetType], "expected Deferred[T], got Deferred with no type"),
        ],
    )
    def test_construct_fails_for_incorrect_type(self, typ, expected_error, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            DeferredTypeHandler(typ, type_handler_factory_mock)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "typ, type_opts, expected_handler_type",
        [
            (Deferred[int], {"foo": 1}, int),
            (Deferred[str], {"foo": 1}, str),
            (Deferred[int | float | str], {"foo": 1}, Union[int, float, str]),
        ],
    )
    def test_construct_with_type_opts(
        self, typ, type_opts, type_handler_factory_mock, type_handler_mock, expected_handler_type
    ):
        type_handler_factory_mock.expect_call(expected_handler_type, **type_opts).will_once(Return(type_handler_mock))
        DeferredTypeHandler(typ, type_handler_factory_mock, **type_opts)

    @pytest.mark.parametrize(
        "typ, handler_name, input_value, output_value",
        [
            (Deferred[int], "int_handler", 0, 0),
            (Deferred[float], "float_handler", 3.14, 3.14),
            (Deferred[float | str], "float_str_handler", "spam", "spam"),
        ],
    )
    def test_parse_value_successfully(self, uut: UUT, input_value, output_value, type_handler_mock, handler_name):
        errors = []
        getattr(type_handler_mock, handler_name).parse.expect_call(errors, loc, input_value).will_once(
            Return(output_value)
        )
        assert uut.parse(errors, loc, input_value) == output_value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ",
        [Deferred[int]],
    )
    def test_parse_unset_successfully(self, uut: UUT):
        errors = []
        assert uut.parse(errors, loc, Unset) == Unset
        assert len(errors) == 0

    @pytest.mark.parametrize("typ", [Deferred[int]])
    def test_accept_unset(self, uut: UUT, visitor_mock):
        visitor_mock.visit_unset.expect_call(loc, Unset)
        uut.accept(visitor_mock, loc, Unset)

    @pytest.mark.parametrize(
        "typ, handler_name, input_value",
        [
            (Deferred[int | float | str], "int_float_str_handler", 1),
            (Deferred[float], "float_handler", 3.14),
            (Deferred[str], "str_handler", "spam"),
        ],
    )
    def test_accept_value(self, uut: UUT, visitor_mock, type_handler_mock, handler_name, input_value):
        getattr(type_handler_mock, handler_name).accept.expect_call(visitor_mock, loc, input_value)
        uut.accept(visitor_mock, loc, input_value)

    @pytest.mark.parametrize("typ", [Deferred[int]])
    def test_validate_fails_if_value_is_unset(self, uut: UUT):
        errors = []
        assert uut.validate(errors, loc, Unset) is False
        assert errors == [ErrorFactory.unset_not_allowed(loc, int)]

    @pytest.mark.parametrize("typ", [Deferred[int]])
    def test_validate_passes_if_value_has_the_right_type(self, uut: UUT):
        errors = []
        assert uut.validate(errors, loc, 123) is True
        assert errors == []

    @pytest.mark.parametrize("validation_status", [True, False])
    def test_validate_forwards_call_to_nested_type_if_its_handler_supports_validation(
        self, type_handler_factory_mock, mock, validation_status
    ):

        class AnnotatedHandler(TypeHandlerWithValidation):

            def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
                return value

            def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
                pass

            def validate(self, errors: list[Error], loc: Loc, value: Any) -> bool:
                return mock.validate(errors, loc, value)

        typ = Annotated[int, Ge(0)]
        type_handler_factory_mock.expect_call(typ).will_once(Return(AnnotatedHandler()))
        uut = DeferredTypeHandler(Deferred[typ], type_handler_factory_mock)
        errors = []
        mock.validate.expect_call(errors, loc, 123).will_once(Return(validation_status))
        assert uut.validate(errors, loc, 123) is validation_status
        assert len(errors) == 0


class TestOptionalTypeHandler:
    UUT = OptionalTypeHandler

    @pytest.fixture
    def uut(self, typ, type_handler_mock, type_handler_factory_mock):
        args = get_args(typ)
        assert len(args) == 2
        type_handler_factory_mock.expect_call(args[0]).will_once(Return(type_handler_mock))
        return OptionalTypeHandler(typ, type_handler_factory_mock)

    @pytest.mark.parametrize(
        "typ",
        [
            int,
            StrictOptional[int],
        ],
    )
    def test_construct_fails_if_non_optional_given(self, typ, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            OptionalTypeHandler(typ, type_handler_factory_mock)
        assert str(excinfo.value) == f"expected Optional[T], got {_utils.describe(typ)} instead"

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (Optional[int], {}),
            (Optional[int], {"foo": 1}),
        ],
    )
    def test_construct_with_type_opts(self, typ, type_opts, type_handler_factory_mock, type_handler_mock):
        args = get_args(typ)
        type_handler_factory_mock.expect_call(args[0], **type_opts).will_once(Return(type_handler_mock))
        OptionalTypeHandler(typ, type_handler_factory_mock, **type_opts)

    @pytest.mark.parametrize(
        "typ, value",
        [
            (Optional[int], None),
        ],
    )
    def test_parse_accepts_none_as_valid_value(self, uut: UUT, value):
        errors = []
        assert uut.parse(errors, loc, value) == value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, value",
        [
            (Optional[int], Unset),
        ],
    )
    def test_parse_does_not_accept_unset_as_valid_value(self, uut: UUT, typ, value):
        errors = []
        assert uut.parse(errors, loc, value) == Unset
        assert errors == [ErrorFactory.unset_not_allowed(loc, typ)]

    @pytest.mark.parametrize(
        "typ, value",
        [
            (Optional[int], 123),
        ],
    )
    def test_parse_forwards_call_to_inner_type_handler(self, uut: UUT, value, type_handler_mock):
        errors = []
        type_handler_mock.parse.expect_call(errors, loc, value).will_once(Return(value))
        assert uut.parse(errors, loc, value) == value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, loc, value, visit_name",
        [
            (Optional[int], loc, None, "visit_none"),
        ],
    )
    def test_accept_none(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ, value",
        [
            (Optional[int], 123),
        ],
    )
    def test_accept_forwards_call_to_inner_type_handler(self, uut: UUT, value, type_handler_mock, visitor_mock):
        type_handler_mock.accept.expect_call(visitor_mock, loc, value)
        uut.accept(visitor_mock, loc, value)


class TestLooseOptionalTypeHandler:
    UUT = LooseOptionalTypeHandler

    @pytest.fixture
    def uut(self, typ, type_handler_mock, type_handler_factory_mock):
        args = get_args(typ)
        assert len(args) == 3
        type_handler_factory_mock.expect_call(args[0]).will_once(Return(type_handler_mock))
        return LooseOptionalTypeHandler(typ, type_handler_factory_mock)

    @pytest.mark.parametrize(
        "typ",
        [
            int,
            Optional[int],
            StrictOptional[int],
        ],
    )
    def test_construct_fails_if_non_loose_optional_given(self, typ, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            LooseOptionalTypeHandler(typ, type_handler_factory_mock)
        assert str(excinfo.value) == f"expected LooseOptional[T], got {_utils.describe(typ)} instead"

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (LooseOptional[int], {}),
            (LooseOptional[int], {"foo": 1}),
        ],
    )
    def test_construct_with_type_opts(self, typ, type_opts, type_handler_factory_mock, type_handler_mock):
        args = get_args(typ)
        type_handler_factory_mock.expect_call(args[0], **type_opts).will_once(Return(type_handler_mock))
        LooseOptionalTypeHandler(typ, type_handler_factory_mock, **type_opts)

    @pytest.mark.parametrize(
        "typ, value",
        [
            (LooseOptional[int], Unset),
            (LooseOptional[int], None),
        ],
    )
    def test_parse_accepts_unset_and_none_as_valid_values(self, uut: UUT, value):
        errors = []
        assert uut.parse(errors, loc, value) == value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, value",
        [
            (LooseOptional[int], 123),
        ],
    )
    def test_parse_forwards_call_to_inner_type_handler(self, uut: UUT, value, type_handler_mock):
        errors = []
        type_handler_mock.parse.expect_call(errors, loc, value).will_once(Return(value))
        assert uut.parse(errors, loc, value) == value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, loc, value, visit_name",
        [
            (LooseOptional[int], loc, Unset, "visit_unset"),
            (LooseOptional[int], loc, None, "visit_none"),
        ],
    )
    def test_accept_unset_or_none(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ, value",
        [
            (LooseOptional[int], 123),
        ],
    )
    def test_accept_forwards_call_to_inner_type_handler(self, uut: UUT, value, type_handler_mock, visitor_mock):
        type_handler_mock.accept.expect_call(visitor_mock, loc, value)
        uut.accept(visitor_mock, loc, value)


class TestStrictOptionalTypeHandler:
    UUT = StrictOptionalTypeHandler

    @pytest.fixture
    def uut(self, typ, type_handler_mock, type_handler_factory_mock):
        args = get_args(typ)
        assert len(args) == 2
        type_handler_factory_mock.expect_call(args[0]).will_once(Return(type_handler_mock))
        return StrictOptionalTypeHandler(typ, type_handler_factory_mock)

    @pytest.mark.parametrize(
        "typ",
        [
            int,
            Optional[int],
        ],
    )
    def test_construct_fails_if_non_strict_optional_given(self, typ, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            StrictOptionalTypeHandler(typ, type_handler_factory_mock)
        assert str(excinfo.value) == f"expected StrictOptional[T], got {_utils.describe(typ)} instead"

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (StrictOptional[int], {}),
            (StrictOptional[int], {"foo": 1}),
        ],
    )
    def test_construct_with_type_opts(self, typ, type_opts, type_handler_factory_mock, type_handler_mock):
        args = get_args(typ)
        type_handler_factory_mock.expect_call(args[0], **type_opts).will_once(Return(type_handler_mock))
        StrictOptionalTypeHandler(typ, type_handler_factory_mock, **type_opts)

    @pytest.mark.parametrize(
        "typ, value",
        [
            (StrictOptional[int], Unset),
        ],
    )
    def test_parse_accepts_unset_as_valid_value(self, uut: UUT, value):
        errors = []
        assert uut.parse(errors, loc, value) == value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, value",
        [
            (StrictOptional[int], None),
        ],
    )
    def test_parse_does_not_accept_none_as_valid_value(self, uut: UUT, typ, value):
        errors = []
        assert uut.parse(errors, loc, value) == Unset
        assert errors == [ErrorFactory.none_not_allowed(loc, typ)]

    @pytest.mark.parametrize(
        "typ, value",
        [
            (StrictOptional[int], 123),
        ],
    )
    def test_parse_forwards_call_to_inner_type_handler(self, uut: UUT, value, type_handler_mock):
        errors = []
        type_handler_mock.parse.expect_call(errors, loc, value).will_once(Return(value))
        assert uut.parse(errors, loc, value) == value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ, loc, value, visit_name",
        [
            (StrictOptional[int], loc, Unset, "visit_unset"),
        ],
    )
    def test_accept_unset(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize(
        "typ, value",
        [
            (StrictOptional[int], 123),
        ],
    )
    def test_accept_forwards_call_to_inner_type_handler(self, uut: UUT, value, type_handler_mock, visitor_mock):
        type_handler_mock.accept.expect_call(visitor_mock, loc, value)
        uut.accept(visitor_mock, loc, value)


class TestUnionTypeHandler:
    UUT = UnionTypeHandler

    @pytest.fixture
    def uut(self, typ, type_handler_mock, type_handler_factory_mock):
        for inner_typ in get_args(typ):
            type_handler_factory_mock.expect_call(inner_typ).will_once(
                Return(getattr(type_handler_mock, f"{inner_typ.__name__}_handler"))
            )
        return UnionTypeHandler(typ, type_handler_factory_mock)

    @pytest.mark.parametrize(
        "typ",
        [
            int,
            Annotated[int, "spam"],
        ],
    )
    def test_construct_fails_if_non_union_given(self, typ, type_handler_factory_mock):
        with pytest.raises(TypeError) as excinfo:
            UnionTypeHandler(typ, type_handler_factory_mock)
        assert str(excinfo.value) == f"expected Union[T, ...], got {_utils.describe(typ)} instead"

    @pytest.mark.parametrize(
        "typ, type_opts",
        [
            (Union[int, float, str], {}),
            (Union[int, float, str], {"foo": 1}),
        ],
    )
    def test_construct_with_type_opts(self, typ, type_opts, type_handler_factory_mock, type_handler_mock):
        args = get_args(typ)
        for x in args:
            type_handler_factory_mock.expect_call(x, **type_opts).will_once(
                Return(getattr(type_handler_mock, x.__name__))
            )
        UnionTypeHandler(typ, type_handler_factory_mock, **type_opts)

    @pytest.mark.parametrize(
        "typ, value",
        [
            (Union[str, int, float], "spam"),
            (Union[str, int, float], 123),
            (Union[str, int, float], 3.14),
        ],
    )
    def test_parse_returns_unchanged_value_if_value_type_matches_one_of_union_types(self, uut: UUT, value):
        errors = []
        assert uut.parse(errors, loc, value) == value
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ",
        [
            Union[int, float],
        ],
    )
    def test_parse_calls_first_inner_handler_and_returns_its_value(self, uut: UUT, type_handler_mock):
        errors = []
        type_handler_mock.int_handler.parse.expect_call(_, loc, "123").will_once(Return(123))
        assert uut.parse(errors, loc, "123") == 123
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ",
        [
            Union[int, float],
        ],
    )
    def test_parse_asks_second_inner_handler_if_first_got_returned_unset(self, uut: UUT, type_handler_mock):
        errors = []
        type_handler_mock.int_handler.parse.expect_call(_, loc, "3.14").will_once(Return(Unset))
        type_handler_mock.float_handler.parse.expect_call(_, loc, "3.14").will_once(Return(3.14))
        assert uut.parse(errors, loc, "3.14") == 3.14
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "typ",
        [
            Union[int, float],
        ],
    )
    def test_parsing_ends_with_error_if_none_of_inner_handler_matched(self, uut: UUT, type_handler_mock):
        errors = []
        type_handler_mock.int_handler.parse.expect_call(_, loc, "spam").will_once(Return(Unset))
        type_handler_mock.float_handler.parse.expect_call(_, loc, "spam").will_once(Return(Unset))
        assert uut.parse(errors, loc, "spam") == Unset
        assert errors == [ErrorFactory.invalid_type(loc, "spam", [int, float])]

    @pytest.mark.parametrize(
        "typ, value, handler_name",
        [
            (Union[int, float], 123, "int_handler"),
            (Union[int, float], 3.14, "float_handler"),
        ],
    )
    def test_accept_forwards_call_to_matched_type_handler(
        self, uut: UUT, type_handler_mock, value, handler_name, visitor_mock
    ):
        getattr(type_handler_mock, handler_name).accept.expect_call(visitor_mock, loc, value)
        uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize("typ", [Union[int, float]])
    def test_accept_falls_back_to_visit_any_if_value_did_not_match_any_of_the_inner_handlers(
        self, uut: UUT, visitor_mock
    ):
        visitor_mock.visit_any.expect_call(loc, "spam")
        uut.accept(visitor_mock, loc, "spam")
