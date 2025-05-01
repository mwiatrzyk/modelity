"""Mixin helpers for building custom type descriptors by implicitly
implementing :class:`modelity.interface.ITypeDescriptor` protocol."""

from typing import Any

from modelity.interface import IDumpFilter, IModel
from modelity.loc import Loc
from modelity.error import Error


class StrDumpMixin:
    """A mixin that adds :meth:`modelity.interface.ITypeDescriptor.dump` method
    implementation that dumps values of any type to :class:`str` class simply
    by using ``str(value)`` conversion.

    Suitable for types that are directly convertible to string with no need of
    any special formatting etc.
    """

    def dump(self, loc: Loc, value: Any, filter: IDumpFilter):
        return filter(loc, str(value))


class ExactDumpMixin:
    """A mixin that adds :meth:`modelity.interface.ITypeDescriptor.dump` method
    implementation that dumps values unchanged."""

    def dump(self, loc: Loc, value: Any, filter: IDumpFilter):
        return filter(loc, value)


class EmptyValidateMixin:
    """A mixin that adds :meth:`modelity.interface.ITypeDescriptor.validate`
    method implementation that simply does nothing.

    Suitable for simple types that does not provide any extra validation
    logic.
    """

    def validate(self, root: IModel, ctx: Any, errors: list[Error], loc: Loc, value: Any):
        pass
