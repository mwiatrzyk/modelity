import textwrap
from typing import Annotated, Any, Optional
import pytest

from mockify.api import Raise, ordered

from modelity.constraints import Ge
from modelity.error import ErrorFactory
from modelity.exc import ValidationError
from modelity.helpers import validate
from modelity.hooks import location_validator
from modelity.loc import Loc
from modelity.model import Model


class Dummy(Model):
    bar: int


def test_declare_validator_without_args(mock):

    class SUT(Model):
        foo: int

        @location_validator("foo")
        def _validate_foo():
            mock.foo()

    sut = SUT(foo=1)
    mock.foo.expect_call()
    with ordered(mock):
        validate(sut)


def test_value_error_exception_is_converted_into_error(mock):

    class SUT(Model):
        foo: int

        @location_validator("foo")
        def _validate_foo():
            mock.foo()

    sut = SUT(foo=1)
    mock.foo.expect_call().will_once(Raise(ValueError("an error")))
    with pytest.raises(ValidationError) as excinfo:
        validate(sut)
    assert excinfo.value.errors == (ErrorFactory.exception(Loc("foo"), 1, "an error", ValueError),)


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

        @location_validator("foo")
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


def test_declare_validator_with_all_args(mock):

    class SUT(Model):
        foo: int

        @location_validator("foo")
        def _validate_foo(cls, self, root, ctx, errors, loc, value):
            mock.foo(cls, self, root, ctx, errors, loc, value)

    ctx = object()
    sut = SUT(foo=123)
    mock.foo.expect_call(SUT, sut, sut, ctx, [], Loc("foo"), 123)
    with ordered(mock):
        validate(sut, ctx=ctx)


def test_declare_validator_in_nested_model_with_self_and_root_args(mock):

    class SUT(Model):

        class Nested(Model):
            foo: int

            @location_validator("foo")
            def _validate_foo(self, root):
                mock.foo(self, root)

        nested: Nested

    sut = SUT(nested={"foo": 123})
    mock.foo.expect_call(sut.nested, sut)
    with ordered(mock):
        validate(sut)


def test_validator_matched_to_nested_model_field_is_still_called_with_parent_model_cls_self_and_root(mock):

    class SUT(Model):

        class Nested(Model):
            foo: int

        nested: Nested

        @location_validator("nested.foo")
        def _validate_nested_foo(cls, self, root, loc, value):
            mock.validate_nested_foo(cls, self, root, loc, value)


    sut = SUT(nested=SUT.Nested(foo=123))
    mock.validate_nested_foo.expect_call(SUT, sut, sut, Loc("nested", "foo"), 123)
    with ordered(mock):
        validate(sut)


def test_two_validators_are_executed_in_declaration_order(mock):

    class SUT(Model):
        foo: int

        @location_validator("foo")
        def _validate_foo():
            mock.foo()

        @location_validator("foo")
        def _validate_bar():
            mock.bar()

    sut = SUT(foo=123)
    mock.foo.expect_call()
    mock.bar.expect_call()
    with ordered(mock):
        validate(sut)


def test_inherited_validators_are_executed_in_declaration_order(mock):

    class Base(Model):

        @location_validator("foo")
        def _validate_foo():
            mock.foo()

    class SUT(Base):
        foo: int

        @location_validator("foo")
        def _validate_bar():
            mock.bar()

    sut = SUT(foo=123)
    mock.foo.expect_call()
    mock.bar.expect_call()
    with ordered(mock):
        validate(sut)


def test_validator_declared_without_field_names_is_applied_to_every_model_value(mock):

    class SUT(Model):

        class Nested(Model):
            a: int

        foo: int
        bar: int
        baz: list[int]
        nested: Nested

        @location_validator()
        def _validate_foo(loc, value):
            mock.foo(loc, value)

    sut = SUT(foo=1, bar=2, baz=[3, 4], nested=SUT.Nested(a=5))
    mock.foo.expect_call(Loc("foo"), 1)
    mock.foo.expect_call(Loc("bar"), 2)
    mock.foo.expect_call(Loc("baz", 0), 3)
    mock.foo.expect_call(Loc("baz", 1), 4)
    mock.foo.expect_call(Loc("baz"), [3, 4])
    mock.foo.expect_call(Loc("nested", "a"), 5)
    mock.foo.expect_call(Loc("nested"), sut.nested)
    with ordered(mock):
        validate(sut)


def test_validator_is_not_called_if_value_is_not_set(mock):

    class SUT(Model):
        foo: Optional[int]

        @location_validator("foo")
        def _validate_foo():
            mock.foo()

    sut = SUT()
    mock.foo.expect_call().times(0)
    with ordered(mock):
        validate(sut)


def test_validator_can_be_provided_by_mixin(mock):
    class Mixin:

        @location_validator()
        def _validate_field(loc, value):
            mock.validate_field(loc, value)

    class SUT(Model, Mixin):
        foo: int

    sut = SUT(foo=123)
    mock.validate_field.expect_call(Loc("foo"), 123)
    validate(sut)


def test_validator_runs_for_nested_model_value_if_pattern_matches_and_value_present(mock):

    class Dummy(Model):
        foo: int

    class SUT(Model):
        dummy: Dummy

        @location_validator("dummy.foo")
        def _validate_field(self, loc, value):
            mock.validate_field(self, loc, value)

    sut = SUT(dummy=Dummy(foo=123))
    mock.validate_field.expect_call(sut, Loc("dummy", "foo"), 123)
    validate(sut)


def test_validator_runs_for_each_nested_model_value_if_wildcard_is_used_and_values_exist(mock):

    class Dummy(Model):
        foo: int
        bar: int
        baz: int

    class SUT(Model):
        dummy: Dummy

        @location_validator("dummy.*")
        def _validate_field(self, loc, value):
            mock.validate_field(self, loc, value)

    sut = SUT(dummy=Dummy(foo=1, bar=2, baz=3))
    mock.validate_field.expect_call(sut, Loc("dummy", "foo"), 1)
    mock.validate_field.expect_call(sut, Loc("dummy", "bar"), 2)
    mock.validate_field.expect_call(sut, Loc("dummy", "baz"), 3)
    with ordered(mock):
        validate(sut)


def test_validator_runs_for_each_array_item_if_wildcard_is_used_and_values_exist(mock):

    class SUT(Model):
        items: list[int]

        @location_validator("items.*")
        def _validate_each_item(self, loc, value):
            mock.validate_field(self, loc, value)

    sut = SUT(items=[1, 2, 3])
    mock.validate_field.expect_call(sut, Loc("items", 0), 1)
    mock.validate_field.expect_call(sut, Loc("items", 1), 2)
    mock.validate_field.expect_call(sut, Loc("items", 2), 3)
    with ordered(mock):
        validate(sut)


def test_validator_runs_for_selected_array_item_if_exists(mock):

    class SUT(Model):
        items: list[int]

        @location_validator("items.1")
        def _validate_each_item(self, loc, value):
            mock.validate_field(self, loc, value)

    sut = SUT(items=[1, 2, 3])
    mock.validate_field.expect_call(sut, Loc("items", 1), 2)
    with ordered(mock):
        validate(sut)


def test_when_value_validator_declared_in_root_model_and_nested_model_then_both_are_executed_in_their_scopes(mock):

    class SUT(Model):

        class Foo(Model):

            class Bar(Model):
                spam: int

            bar: list[Bar]

            @location_validator("bar.*.spam")
            def _validate_spam(loc, value):
                mock.validate_spam(loc, value)

        items: list[Foo]
        bar: list[Foo.Bar] = []

        @location_validator("items.*")
        def _validate_items(loc, value):
            mock.validate_items(loc, value)

    sut = SUT(items=[SUT.Foo(bar=[SUT.Foo.Bar(spam=123)])])
    mock.validate_spam.expect_call(Loc("items", 0, "bar", 0, "spam"), 123)
    mock.validate_items.expect_call(Loc("items", 0), sut.items[0])
    with ordered(mock):
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
        (Any, object()),
    ],
)
def test_validator_can_be_used_with_field_of_any_type(typ, value, mock):

    class SUT(Model):
        foo: typ  # type: ignore

        @location_validator("foo")
        def _validate_field(self, loc, value):
            mock.validate_field(self, loc, value)

    sut = SUT(foo=value)
    mock.validate_field.expect_call(sut, Loc("foo"), value)
    validate(sut)
