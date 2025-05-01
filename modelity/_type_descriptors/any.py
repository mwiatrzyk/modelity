from typing import Any
from modelity.interface import IDumpFilter, ITypeDescriptor
from modelity.loc import Loc
from modelity.mixins import EmptyValidateMixin, ExactDumpMixin


def make_any_type_descriptor() -> ITypeDescriptor:

    class AnyTypeDescriptor(ExactDumpMixin, EmptyValidateMixin):
        def parse(self, errors, loc, value):
            return value

    return AnyTypeDescriptor()
