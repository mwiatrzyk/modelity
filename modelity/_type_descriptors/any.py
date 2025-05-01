from typing import Any
from modelity.interface import IDumpFilter, ITypeDescriptor
from modelity.loc import Loc
from modelity.mixins import NoValidateMixin


def make_any_type_descriptor() -> ITypeDescriptor:

    class AnyTypeDescriptor(NoValidateMixin):
        def parse(self, errors, loc, value):
            return value

        def dump(self, loc: Loc, value: Any, filter: IDumpFilter):
            return value

    return AnyTypeDescriptor()
