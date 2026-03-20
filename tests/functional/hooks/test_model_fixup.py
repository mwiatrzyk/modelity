import datetime
import textwrap
from typing import Optional

import pytest

from mockify.api import Raise, Return, Invoke, ordered, _

from modelity.error import Error, ErrorCode, ErrorFactory
from modelity.exc import ParsingError, UserError
from modelity.helpers import fixup
from modelity.hooks import field_postprocessor, field_preprocessor, model_fixup
from modelity.loc import Loc
from modelity.base import Model
from modelity.typing import Deferred
from modelity.unset import Unset


def test_when_hook_raises_error_then_it_propagates(mock):

    class SUT(Model):
        foo: int

        @model_fixup()
        def _model_fixup():
            raise mock()

    mock.expect_call().will_once(Raise(ValueError("an error")))
    with pytest.raises(ValueError) as excinfo:
        SUT(foo=123)


def test_declare_hook_without_args(mock):

    class SUT(Model):
        foo: Deferred[int] = Unset

        @model_fixup()
        def _model_fixup():
            return mock.fixup()

    mock.fixup.expect_call()
    SUT()


@pytest.mark.parametrize(
    "arg_name, expect_call_arg",
    [
        ("cls", "SUT"),
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

    mock.fixup.expect_call({expect_call_arg})
    sut = SUT()
    """
    )
    g = globals()
    g.update({"mock": mock})
    exec(code, g)


def test_declare_hook_with_self_arg(mock):

    class SUT(Model):
        foo: int

        @model_fixup()
        def _fixup(self):
            mock(self.foo)

    mock.expect_call(123)
    SUT(foo=123)


def test_two_hooks_are_chained_in_declaration_order(mock):

    class SUT(Model):
        foo: int

        @model_fixup()
        def _first():
            return mock.first()

        @model_fixup()
        def _second():
            return mock.second()

    mock.first.expect_call()
    mock.second.expect_call()
    with ordered(mock):
        sut = SUT(foo=1)
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

    mock.first.expect_call()
    mock.second.expect_call()
    with ordered(mock):
        sut = SUT(foo=123)
        assert sut.foo == 123


def test_hook_can_be_provided_by_mixin(mock):
    class Mixin:

        @model_fixup()
        def _model_fixup(cls, self, loc):
            return mock.model_fixup(cls, self, loc)

    class SUT(Model, Mixin):
        foo: int

    mock.model_fixup.expect_call(SUT, _, Loc())
    sut = SUT(foo=123)
    assert sut.foo == 123


def test_hook_can_access_model_object_and_set_related_fields():

    class SUT(Model):
        created: datetime.datetime
        modified: Optional[datetime.datetime] = None

        @model_fixup()
        def _set_modified(self):
            self.modified = self.created

    sut = SUT(created=datetime.datetime.now())
    assert sut.modified == sut.created


def test_hook_is_called_after_pre_and_postprocessors(mock):

    class SUT(Model):
        foo: int

        @model_fixup()
        def _fixup_foo(self, loc):
            mock.fixup(loc, self.foo)

        @field_preprocessor("foo")
        def _preprocess_foo(cls, loc, value):
            return mock.pre(loc, value)

        @field_postprocessor("foo")
        def _postprocess_foo(cls, loc, value):
            return mock.post(loc, value)

    mock.pre.expect_call(Loc("foo"), 1).will_once(Return(2))
    mock.post.expect_call(Loc("foo"), 2).will_once(Return(3))
    mock.fixup.expect_call(Loc(), 3)
    with ordered(mock):
        sut = SUT(foo=1)
        assert sut.foo == 3


def test_hook_is_executed_by_fixup_helper(mock):

    class SUT(Model):

        @model_fixup()
        def _model_fixup():
            mock()

    mock.expect_call().times(2)
    sut = SUT()
    fixup(sut)


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

    mock.root.expect_call(Loc()).times(2)
    mock.nested.expect_call(Loc())
    sut = SUT(nested=Nested())
    mock.nested.expect_call(Loc("nested"))
    fixup(sut)
