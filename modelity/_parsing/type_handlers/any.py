from typing import Any

from modelity.base import ModelVisitor, TypeHandler
from modelity.error import Error
from modelity.loc import Loc
from modelity.unset import is_unset


class AnyTypeHandler(TypeHandler):
    def parse(self, errors: list[Error], loc: Loc, value: Any, /):
        return value

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any, /):
        if is_unset(value):
            visitor.visit_unset(loc, value)
        elif value is None:
            visitor.visit_none(loc, value)
        else:
            visitor.visit_any(loc, value)
