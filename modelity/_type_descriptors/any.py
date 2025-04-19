from typing import Any
from modelity.interface import IDumpFilter, ITypeDescriptor
from modelity.loc import Loc


def make_any_type_descriptor() -> ITypeDescriptor:

    class AnyTypeDescriptor:
        def parse(self, errors, loc, value):
            return value

        def dump(self, loc: Loc, value: Any, filter: IDumpFilter):
            return filter(loc, value)

        def validate(self, root, ctx, errors, loc, value):
            return

    return AnyTypeDescriptor()
