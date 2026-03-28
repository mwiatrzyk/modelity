import textwrap
from typing import Optional

import pytest

from mockify.api import Return, ordered

from modelity.helpers import fixup
from modelity.hooks import after_field_set, field_postprocessor, field_preprocessor
from modelity.loc import Loc
from modelity.base import Model
from modelity.typing import Deferred
from modelity.unset import Unset


@pytest.mark.parametrize(
    "exc",
    [
        ValueError("an error"),
        TypeError("an error"),
    ],
)
def test_raised_exception_is_propagated(exc):

    class SUT(Model):
        foo: int

        @after_field_set("foo")
        def _fixup_foo(value):
            raise exc

    with pytest.raises(exc.__class__) as excinfo:
        SUT(foo=123)
    assert excinfo.value == exc


def test_declare_hook_without_args(mock):

    class SUT(Model):
        foo: Deferred[int] = Unset

        @after_field_set("foo")
        def _fixup_foo():
            return mock()

    mock.expect_call()
    sut = SUT(foo=12)
    assert sut.foo == 12


@pytest.mark.parametrize(
    "arg_name, expect_call_arg, given_foo",
    [
        ("cls", "SUT", 1),
        ("loc", "Loc('foo')", 3),
        ("value", 4, 4),
    ],
)
def test_declare_hook_with_single_arg(mock, arg_name, expect_call_arg, given_foo):
    code = textwrap.dedent(
        f"""
    class SUT(Model):
        foo: Deferred[int] = Unset

        @after_field_set("foo")
        def _fixup_foo({arg_name}):
            return mock({arg_name})

    mock.expect_call({expect_call_arg})
    sut = SUT(foo={given_foo!r})
    assert sut.foo == {given_foo!r}
    """
    )
    g = globals()
    g.update({"mock": mock})
    exec(code, g)


def test_declare_hook_with_self_arg(mock):

    class SUT(Model):
        foo: Deferred[int] = Unset

        @after_field_set("foo")
        def _fixup_foo(self):
            return mock(self)

    sut = SUT()
    mock.expect_call(sut)
    sut.foo = 12
    assert sut.foo == 12


def test_hook_declared_without_field_names_is_executed_for_all_fields(mock):

    class SUT(Model):
        foo: int
        bar: int

        @after_field_set()
        def _fixup_any(loc, value):
            return mock(loc, value)

    mock.expect_call(Loc("foo"), 1)
    mock.expect_call(Loc("bar"), 2)
    with ordered(mock):
        sut = SUT(foo=1, bar=2)
        assert sut.foo == 1
        assert sut.bar == 2


def test_two_hooks_are_chained_in_declaration_order(mock):

    class SUT(Model):
        foo: int

        @after_field_set("foo")
        def _first(value):
            return mock.first(value)

        @after_field_set("foo")
        def _second(value):
            return mock.second(value)

    mock.first.expect_call(1)
    mock.second.expect_call(1)
    with ordered(mock):
        sut = SUT(foo=1)
        assert sut.foo == 1


def test_inherited_hooks_are_chained_in_declaration_order(mock):

    class Base(Model):

        @after_field_set()
        def _first(value):
            return mock.first(value)

    class SUT(Base):
        foo: int

        @after_field_set("foo")
        def _second(value):
            return mock.second(value)

    mock.first.expect_call(123)
    mock.second.expect_call(123)
    with ordered(mock):
        sut = SUT(foo=123)
        assert sut.foo == 123


def test_hook_can_be_provided_by_mixin(mock):
    class Mixin:

        @after_field_set()
        def _fixup_any(loc, value):
            return mock(loc, value)

    class SUT(Model, Mixin):
        foo: int

    mock.expect_call(Loc("foo"), 123)
    sut = SUT(foo=123)
    assert sut.foo == 123


def test_hook_is_called_after_pre_and_postprocessors(mock):

    class SUT(Model):
        foo: int

        @after_field_set("foo")
        def _fixup_foo(self, loc, value):
            mock.fixup(loc, value)

        @field_preprocessor("foo")
        def _preprocess_foo(cls, loc, value):
            return mock.pre(loc, value)

        @field_postprocessor("foo")
        def _postprocess_foo(cls, loc, value):
            return mock.post(loc, value)

    mock.pre.expect_call(Loc("foo"), 1).will_once(Return(2))
    mock.post.expect_call(Loc("foo"), 2).will_once(Return(3))
    mock.fixup.expect_call(Loc("foo"), 3)
    with ordered(mock):
        sut = SUT(foo=1)
        assert sut.foo == 3


def test_hook_is_not_called_if_field_is_not_set(mock):

    class SUT(Model):
        foo: int
        bar: Deferred[int] = Unset
        baz: Deferred[int] = Unset

        @after_field_set("foo")
        def _fixup_foo(loc, value):
            mock.foo(loc, value)

        @after_field_set("bar")
        def _fixup_bar(loc, value):
            mock.bar(loc, value)

        @after_field_set("baz")
        def _fixup_baz(loc, value):
            mock.baz(loc, value)

    mock.foo.expect_call(Loc("foo"), 123)
    sut = SUT(foo=123)
    mock.bar.expect_call(Loc("bar"), 456)
    sut.bar = 456
    mock.baz.expect_call(Loc("baz"), 789)
    sut.baz = 789
