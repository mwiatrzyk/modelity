import textwrap

import pytest

from mockify.api import Raise, ordered

from modelity.error import Error, ErrorCode, ErrorFactory
from modelity.exc import UserError, ValidationError
from modelity.helpers import validate
from modelity.hooks import model_postvalidator
from modelity.loc import Loc
from modelity.model import Model
from modelity.unset import Unset


@pytest.mark.parametrize(
    "factory, expected_error",
    [
        (lambda: UserError("a message"), Error(Loc(), ErrorCode.USER_ERROR, "a message")),
        (
            lambda: UserError("a message", code=ErrorCode.PARSE_ERROR),
            Error(Loc(), ErrorCode.PARSE_ERROR, "a message"),
        ),
        (
            lambda: UserError("a message", loc=Loc("bar")),
            Error(Loc("bar"), ErrorCode.USER_ERROR, "a message"),
        ),
        (
            lambda: UserError("a message", value=456),
            Error(Loc(), ErrorCode.USER_ERROR, "a message", 456),
        ),
        (
            lambda: UserError("a message", data={"min": 0, "max": 10}),
            Error(Loc(), ErrorCode.USER_ERROR, "a message", data={"min": 0, "max": 10}),
        ),
    ],
)
def test_user_error_raised_is_converted_to_error(factory, expected_error):

    class SUT(Model):
        foo: int

        @model_postvalidator()
        def _model_postvalidator():
            raise factory()

    sut = SUT(foo=123)
    with pytest.raises(ValidationError) as excinfo:
        validate(sut)
    assert excinfo.value.errors == (expected_error,)


def test_invoke_model_postvalidator_without_args(mock):

    class SUT(Model):

        @model_postvalidator()
        def foo():
            mock.foo()

    sut = SUT()
    mock.foo.expect_call()
    with ordered(mock):
        validate(sut)


def test_value_error_exception_is_converted_into_error(mock):

    class SUT(Model):

        @model_postvalidator()
        def foo():
            mock.foo()

    sut = SUT()
    mock.foo.expect_call().will_once(Raise(ValueError("an error")))
    with pytest.raises(ValidationError) as excinfo:
        validate(sut)
    assert excinfo.value.errors == (ErrorFactory.exception(Loc(), Unset, ValueError("an error")),)


@pytest.mark.parametrize(
    "arg_name, expect_call_arg",
    [
        ("cls", "SUT"),
        ("self", "sut"),
        ("root", "sut"),
        ("ctx", "{1, 2, 3}"),
        ("errors", "[]"),
        ("loc", "Loc()"),
    ],
)
def test_invoke_model_postvalidator_with_single_arg(mock, arg_name, expect_call_arg):
    code = textwrap.dedent(
        f"""
    class SUT(Model):

        @model_postvalidator()
        def foo({arg_name}):
            mock.foo({arg_name})

    sut = SUT()
    mock.foo.expect_call({expect_call_arg})
    with ordered(mock):
        validate(sut, ctx=ctx)
    """
    )
    ctx = {1, 2, 3}
    g = dict(globals())
    g.update({"mock": mock, "ctx": ctx})
    exec(code, g)


def test_invoke_nested_model_postvalidator_with_self_and_root_arguments(mock):

    class SUT(Model):

        class Nested(Model):
            @model_postvalidator()
            def foo(self, root):
                mock.foo(self, root)

        nested: Nested

    sut = SUT(nested={})
    mock.foo.expect_call(sut.nested, sut)
    with ordered(mock):
        validate(sut)


def test_invoke_model_postvalidator_with_all_params(mock):

    class SUT(Model):

        @model_postvalidator()
        def foo(cls, self, root, ctx, errors, loc):
            mock.foo(cls, self, root, ctx, errors, loc)

    sut = SUT()
    mock.foo.expect_call(SUT, sut, sut, None, [], Loc())
    with ordered(mock):
        validate(sut)


def test_two_model_postvalidators_are_executed_in_declaration_order(mock):

    class SUT(Model):

        @model_postvalidator()
        def foo():
            mock.foo()

        @model_postvalidator()
        def bar():
            mock.bar()

    sut = SUT()
    mock.foo.expect_call()
    mock.bar.expect_call()
    with ordered(mock):
        validate(sut)


def test_postvalidators_defined_in_base_model_are_also_executed_for_child_model(mock):

    class Base(Model):

        @model_postvalidator()
        def foo():
            mock.foo()

    class SUT(Base):

        @model_postvalidator()
        def bar():
            mock.bar()

    sut = SUT()
    mock.foo.expect_call()
    mock.bar.expect_call()
    with ordered(mock):
        validate(sut)


def test_model_postvalidator_can_be_provided_by_mixin(mock):
    class Mixin:

        @model_postvalidator()
        def _postvalidate_model():
            mock.postvalidate_model()

    class SUT(Model, Mixin):
        foo: int

    sut = SUT(foo=123)
    mock.postvalidate_model.expect_call()
    validate(sut)
