from typing import Any

from modelity.base import ModelVisitor, TypeHandler
from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset


class UnsetTypeHandler(TypeHandler):
    def parse(self, errors: list[Error], loc: Loc, value: Any):
        if value is Unset:
            return value
        errors.append(ErrorFactory.invalid_value(loc, value, [Unset]))
        return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visitor.visit_unset(loc, value)
