from typing import Any
from modelity.interface import ITypeDescriptor, IModelVisitor
from modelity.loc import Loc


def make_any_type_descriptor() -> ITypeDescriptor:
    """Make descriptor for any Python type.

    This is used for fields that are declared using :class:`typing.Any` type
    annotation.
    """

    class AnyTypeDescriptor:
        def parse(self, errors, loc, value):
            return value

        def accept(self, loc: Loc, value: Any, visitor: IModelVisitor):
            visitor.visit_scalar(loc, value)

        def validate(self, errors, loc, value):
            return None

    return AnyTypeDescriptor()
