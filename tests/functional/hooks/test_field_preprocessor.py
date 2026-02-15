import textwrap

import pytest

from mockify.api import Raise, Return, ordered

from modelity.error import Error, ErrorCode, ErrorFactory
from modelity.exc import ParsingError, UserError
from modelity.hooks import field_preprocessor
from modelity.loc import Loc
from modelity.model import Model
from modelity.types import Deferred
from modelity.unset import Unset


@pytest.mark.parametrize(
    "factory, expected_error",
    [
        (lambda: UserError("a message"), Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", "spam", {})),
        (
            lambda: UserError("a message", code=ErrorCode.PARSE_ERROR),
            Error(Loc("foo"), ErrorCode.PARSE_ERROR, "a message", "spam", {}),
        ),
        (
            lambda: UserError("a message", loc=Loc("bar")),
            Error(Loc("bar"), ErrorCode.USER_ERROR, "a message", "spam", {}),
        ),
        (
            lambda: UserError("a message", value=123),
            Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", 123, {}),
        ),
        (
            lambda: UserError("a message", data={"min": 0, "max": 10}),
            Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", "spam", {"min": 0, "max": 10}),
        ),
    ],
)
def test_user_error_raised_is_converted_to_error(factory, expected_error):

    class SUT(Model):
        foo: int

        @field_preprocessor("foo")
        def _preprocess_foo(value):
            raise factory()

    with pytest.raises(ParsingError) as excinfo:
        SUT(foo="spam")
    assert excinfo.value.errors == (expected_error,)


def test_declare_preprocessor_without_args(mock):

    class SUT(Model):
        foo: Deferred[int] = Unset

        @field_preprocessor("foo")
        def _preprocess():
            return mock.preprocess()

    sut = SUT()
    mock.preprocess.expect_call().will_once(Return("123"))
    sut.foo = 1
    assert sut.foo == 123


@pytest.mark.parametrize(
    "arg_name, expect_call_arg, given_foo, mock_return, expected_foo",
    [
        ("cls", "SUT", 1, "123", 123),
        ("errors", "[]", 1, "123", 123),
        ("loc", "Loc('foo')", 1, "123", 123),
        ("value", 1, 1, "123", 123),
        ("value", 2, 2, "2", 2),
    ],
)
def test_declare_preprocessor_with_single_arg(mock, arg_name, expect_call_arg, given_foo, mock_return, expected_foo):
    code = textwrap.dedent(
        f"""
    class SUT(Model):
        foo: Deferred[int] = Unset

        @field_preprocessor("foo")
        def _preprocess({arg_name}):
            return mock.preprocess({arg_name})

    sut = SUT()
    mock.preprocess.expect_call({expect_call_arg}).will_once(Return({mock_return!r}))
    sut.foo = {given_foo!r}
    assert sut.foo == {expected_foo!r}
    """
    )
    g = globals()
    g.update({"mock": mock})
    exec(code, g)


def test_preprocessor_declared_without_field_names_is_executed_for_all_fields(mock):

    class SUT(Model):
        foo: int
        bar: int

        @field_preprocessor()
        def _preprocess(loc, value):
            return mock.foo(loc, value)

    mock.foo.expect_call(Loc("foo"), 1).will_once(Return(1))
    mock.foo.expect_call(Loc("bar"), 2).will_once(Return(2))
    with ordered(mock):
        sut = SUT(foo=1, bar=2)
        assert sut.foo == 1
        assert sut.bar == 2


def test_two_preprocessors_are_chained_in_declaration_order(mock):

    class SUT(Model):
        foo: int

        @field_preprocessor("foo")
        def _first(value):
            return mock.first(value)

        @field_preprocessor("foo")
        def _second(value):
            return mock.second(value)

    mock.first.expect_call(1).will_once(Return(12))
    mock.second.expect_call(12).will_once(Return(123))
    with ordered(mock):
        sut = SUT(foo=1)
        assert sut.foo == 123


def test_inherited_preprocessors_are_chained_in_declaration_order(mock):

    class Base(Model):

        @field_preprocessor()
        def _first(value):
            return mock.first(value)

    class SUT(Base):
        foo: int

        @field_preprocessor("foo")
        def _second(value):
            return mock.second(value)

    mock.first.expect_call(1).will_once(Return(12))
    mock.second.expect_call(12).will_once(Return(123))
    with ordered(mock):
        sut = SUT(foo=1)
        assert sut.foo == 123


def test_when_preprocessor_throws_type_error_then_it_is_converted_to_error(mock):

    class SUT(Model):
        foo: Deferred[int] = Unset

        @field_preprocessor("foo")
        def _preprocess_foo(value):
            return mock.preprocess_foo(value)

    mock.preprocess_foo.expect_call(123).will_once(Raise(TypeError("an error")))
    sut = SUT()
    with pytest.raises(ParsingError) as excinfo:
        sut.foo = 123
    assert excinfo.value.typ is SUT
    assert excinfo.value.errors == (ErrorFactory.exception(Loc("foo"), 123, TypeError("an error")),)


def test_field_preprocessor_can_be_provided_by_mixin(mock):
    class Mixin:

        @field_preprocessor()
        def _preprocess_field(loc, value):
            return mock.preprocess_field(loc, value)

    class SUT(Model, Mixin):
        foo: int

    mock.preprocess_field.expect_call(Loc("foo"), "123").will_once(Return("456"))
    sut = SUT(foo="123")
    assert sut.foo == 456
