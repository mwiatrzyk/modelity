from typing import Any

from modelity.base import ModelVisitor, TypeHandler
from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType


class NoneTypeHandler(TypeHandler):

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if value is None:
            return value
        errors.append(ErrorFactory.invalid_value(loc, value, [None]))
        return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visitor.visit_none(loc, value)
