import textwrap
from typing import Annotated

import pytest

from mockify.api import Raise, ordered

from modelity.constraints import Ge
from modelity.error import Error, ErrorCode, ErrorFactory
from modelity.exc import UserError, ValidationError
from modelity.helpers import validate
from modelity.hooks import field_validator
from modelity.loc import Loc
from modelity.model import Model
from modelity.types import LooseOptional
from modelity.unset import Unset


class Dummy(Model):
    bar: int


@pytest.mark.parametrize(
    "factory, expected_error",
    [
        (lambda: UserError("a message"), Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", 123)),
        (
            lambda: UserError("a message", code=ErrorCode.PARSE_ERROR),
            Error(Loc("foo"), ErrorCode.PARSE_ERROR, "a message", 123),
        ),
        (
            lambda: UserError("a message", loc=Loc("bar")),
            Error(Loc("bar"), ErrorCode.USER_ERROR, "a message", 123),
        ),
        (
            lambda: UserError("a message", value=456),
            Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", 456),
        ),
        (
            lambda: UserError("a message", data={"min": 0, "max": 10}),
            Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", 123, data={"min": 0, "max": 10}),
        ),
    ],
)
def test_user_error_raised_is_converted_to_error(factory, expected_error):

    class SUT(Model):
        foo: int

        @field_validator("foo")
        def _field_validator():
            raise factory()

    sut = SUT(foo=123)
    with pytest.raises(ValidationError) as excinfo:
        validate(sut)
    assert excinfo.value.errors == (expected_error,)


def test_declare_field_validator_without_args(mock):

    class SUT(Model):
        foo: int

        @field_validator("foo")
        def _validate_foo():
            mock.foo()

    sut = SUT(foo=1)
    mock.foo.expect_call()
    with ordered(mock):
        validate(sut)


def test_value_error_exception_is_converted_into_error(mock):

    class SUT(Model):
        foo: int

        @field_validator("foo")
        def _validate_foo():
            mock.foo()

    sut = SUT(foo=1)
    mock.foo.expect_call().will_once(Raise(ValueError("an error")))
    with pytest.raises(ValidationError) as excinfo:
        validate(sut)
    assert excinfo.value.errors == (ErrorFactory.exception(Loc("foo"), 1, ValueError("an error")),)


@pytest.mark.parametrize(
    "arg_name, expected_call_arg",
    [
        ("cls", "SUT"),
        ("self", "sut"),
        ("root", "sut"),
        ("ctx", "{1, 2, 3}"),
        ("errors", "[]"),
        ("loc", "Loc('foo')"),
        ("value", "123"),
    ],
)
def test_declare_field_validator_with_single_arg(mock, arg_name, expected_call_arg):
    code = textwrap.dedent(
        f"""
    class SUT(Model):
        foo: int

        @field_validator("foo")
        def _validate_foo({arg_name}):
            mock.foo({arg_name})

    sut = SUT(foo=123)
    assert sut.foo == 123
    mock.foo.expect_call({expected_call_arg})
    with ordered(mock):
        validate(sut, ctx=ctx)
    """
    )
    ctx = {1, 2, 3}
    g = dict(globals())
    g.update({"mock": mock, "ctx": ctx})
    exec(code, g)


def test_declare_field_validator_with_all_args(mock):

    class SUT(Model):
        foo: int

        @field_validator("foo")
        def _validate_foo(cls, self, root, ctx, errors, loc, value):
            mock.foo(cls, self, root, ctx, errors, loc, value)

    ctx = object()
    sut = SUT(foo=123)
    mock.foo.expect_call(SUT, sut, sut, ctx, [], Loc("foo"), 123)
    with ordered(mock):
        validate(sut, ctx=ctx)


def test_declare_field_validator_in_nested_model_with_self_and_root_args(mock):

    class SUT(Model):

        class Nested(Model):
            foo: int

            @field_validator("foo")
            def _validate_foo(self, root):
                mock.foo(self, root)

        nested: Nested

    sut = SUT(nested={"foo": 123})
    mock.foo.expect_call(sut.nested, sut)
    with ordered(mock):
        validate(sut)


def test_two_field_validators_are_executed_in_declaration_order(mock):

    class SUT(Model):
        foo: int

        @field_validator("foo")
        def _validate_foo():
            mock.foo()

        @field_validator("foo")
        def _validate_bar():
            mock.bar()

    sut = SUT(foo=123)
    mock.foo.expect_call()
    mock.bar.expect_call()
    with ordered(mock):
        validate(sut)


def test_inherited_field_validators_are_executed_in_declaration_order(mock):

    class Base(Model):

        @field_validator()
        def _validate_foo():
            mock.foo()

    class SUT(Base):
        foo: int

        @field_validator("foo")
        def _validate_bar():
            mock.bar()

    sut = SUT(foo=123)
    mock.foo.expect_call()
    mock.bar.expect_call()
    with ordered(mock):
        validate(sut)


def test_field_validator_declared_without_field_names_is_applied_to_all_fields(mock):

    class SUT(Model):
        foo: int
        bar: int

        @field_validator()
        def _validate_foo(loc, value):
            mock.foo(loc, value)

    sut = SUT(foo=123, bar=456)
    mock.foo.expect_call(Loc("foo"), 123)
    mock.foo.expect_call(Loc("bar"), 456)
    with ordered(mock):
        validate(sut)


def test_field_validator_is_not_called_if_value_is_not_set(mock):

    class SUT(Model):
        foo: LooseOptional[int]

        @field_validator("foo")
        def _validate_foo():
            mock.foo()

    sut = SUT(foo=Unset)
    mock.foo.expect_call().times(0)
    with ordered(mock):
        validate(sut)


def test_field_validator_can_be_provided_by_mixin(mock):
    class Mixin:

        @field_validator()
        def _validate_field(loc, value):
            mock.validate_field(loc, value)

    class SUT(Model, Mixin):
        foo: int

    sut = SUT(foo=123)
    mock.validate_field.expect_call(Loc("foo"), 123)
    validate(sut)


@pytest.mark.skip
def test_run_field_validator_declared_with_nested_model_field_name_runs_if_that_field_is_set(mock):

    class Dummy(Model):
        foo: int

    class SUT(Model):
        dummy: Dummy

        @field_validator("dummy.foo")
        def _validate_field(loc, value):
            mock.validate_field(loc, value)

    sut = SUT(dummy=Dummy(foo=123))
    mock.validate_field.expect_call(sut, Loc("dummy", "foo"), 123)
    validate(sut)


@pytest.mark.parametrize(
    "typ, value",
    [
        (Dummy, Dummy(bar=123)),
        (dict[str, int], {"one": 1}),
        (dict[str, list[str]], {"one": ["two", "three"]}),
        (list[int], [1, 2, 3]),
        (set[int], {1, 2, 3}),
        (Annotated[int, Ge(0)], 0),
        (str, "spam"),
        (int, 123),
        (bool, True),
        (type(None), None),
    ],
)
def test_field_validator_can_be_used_with_field_of_any_type(typ, value, mock):

    class SUT(Model):
        foo: typ  # type: ignore

        @field_validator("foo")
        def _validate_field(loc, value):
            mock.validate_field(loc, value)

    sut = SUT(foo=value)
    mock.validate_field.expect_call(Loc("foo"), value)
    validate(sut)
