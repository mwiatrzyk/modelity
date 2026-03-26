import datetime
import textwrap
from typing import Optional

import pytest

from mockify.api import Raise, Return, ordered, _

from modelity.helpers import fixup
from modelity.hooks import field_postprocessor, field_preprocessor, model_fixup
from modelity.loc import Loc
from modelity.base import Model
from modelity.typing import Deferred
from modelity.unset import Unset


@pytest.mark.parametrize("exc", [
    ValueError("a value error"),
    TypeError("a type error"),
])
def test_when_hook_raises_error_then_it_propagates(mock, exc):

    class SUT(Model):
        foo: int

        @model_fixup()
        def _model_fixup():
            raise mock()

    sut = SUT(foo=123)
    mock.expect_call().will_once(Raise(exc))
    with pytest.raises(exc.__class__) as excinfo:
        fixup(sut)
    assert excinfo.value == exc


def test_declare_hook_without_args(mock):

    class SUT(Model):
        foo: Deferred[int] = Unset

        @model_fixup()
        def _model_fixup():
            return mock.fixup()

    sut = SUT()
    mock.fixup.expect_call()
    fixup(sut)


@pytest.mark.parametrize(
    "arg_name, expect_call_arg",
    [
        ("cls", "SUT"),
        ("self", "sut"),
        ("root", "sut"),
        ("ctx", "ctx"),
        ("loc", "Loc()"),
    ],
)
def test_declare_hook_with_single_arg(mock, arg_name, expect_call_arg):
    code = textwrap.dedent(
        f"""
    class SUT(Model):

        @model_fixup()
        def _model_fixup({arg_name}):
            mock.fixup({arg_name})

    ctx = object()
    sut = SUT()
    mock.fixup.expect_call({expect_call_arg})
    fixup(sut, ctx)
    """
    )
    g = globals()
    g.update({"mock": mock})
    exec(code, g)


def test_two_hooks_are_chained_in_declaration_order(mock):

    class SUT(Model):
        foo: int

        @model_fixup()
        def _first():
            return mock.first()

        @model_fixup()
        def _second():
            return mock.second()

    sut = SUT(foo=1)
    mock.first.expect_call()
    mock.second.expect_call()
    with ordered(mock):
        fixup(sut)
        assert sut.foo == 1


def test_inherited_hooks_are_chained_in_declaration_order(mock):

    class Base(Model):

        @model_fixup()
        def _first():
            return mock.first()

    class SUT(Base):
        foo: int

        @model_fixup()
        def _second():
            return mock.second()

    sut = SUT(foo=123)
    mock.first.expect_call()
    mock.second.expect_call()
    with ordered(mock):
        fixup(sut)
        assert sut.foo == 123


def test_hook_can_be_provided_by_mixin(mock):
    class Mixin:

        @model_fixup()
        def _model_fixup(cls, self, loc):
            return mock.model_fixup(cls, self, loc)

    class SUT(Model, Mixin):
        foo: int

    sut = SUT(foo=123)
    mock.model_fixup.expect_call(SUT, _, Loc())
    fixup(sut)
    assert sut.foo == 123


def test_hook_can_access_model_object_and_set_related_fields():

    class SUT(Model):
        created: datetime.datetime
        modified: Optional[datetime.datetime] = None

        @model_fixup()
        def _set_modified(self):
            self.modified = self.created

    sut = SUT(created=datetime.datetime.now())
    fixup(sut)
    assert sut.modified == sut.created


def test_fixup_hook_in_nested_model_is_executed_by_fixup_helper(mock):

    class Nested(Model):

        @model_fixup()
        def _model_fixup(loc):
            mock.nested(loc)

    class SUT(Model):
        nested: Nested

        @model_fixup()
        def _model_fixup(loc):
            mock.root(loc)

    sut = SUT(nested=Nested())
    mock.root.expect_call(Loc())
    mock.nested.expect_call(Loc("nested"))
    fixup(sut)


def test_fixup_hook_in_nested_model_can_access_root_model(mock):

    class Nested(Model):

        @model_fixup()
        def _model_fixup(root):
            mock(root)

    class SUT(Model):
        nested: Nested

    sut = SUT(nested=Nested())
    mock.expect_call(sut)
    fixup(sut)


def test_fixup_hook_in_nested_model_can_access_context_object(mock):

    class Nested(Model):

        @model_fixup()
        def _model_fixup(ctx):
            mock(ctx)

    class SUT(Model):
        nested: Nested

    ctx = object()
    sut = SUT(nested=Nested())
    mock.expect_call(ctx)
    fixup(sut, ctx=ctx)
