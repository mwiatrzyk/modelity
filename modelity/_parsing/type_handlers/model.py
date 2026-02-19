from typing import Any, Mapping

from modelity.base import Model, ModelVisitor, TypeHandler
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType


class ModelTypeHandler(TypeHandler):

    def __init__(self, model_type: type[Model]):
        self._model_type = model_type

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if isinstance(value, self._model_type):
            return value
        if not isinstance(value, Mapping):
            errors.append(ErrorFactory.invalid_type(loc, value, [self._model_type], [Mapping]))
            return Unset
        try:
            return self._model_type(**value)
        except ParsingError as e:
            errors.extend(Error(loc + x.loc, x.code, x.msg, x.value, x.data) for x in e.errors)
            return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        if isinstance(value, self._model_type):
            value.accept(visitor, loc)  # type: ignore
        else:
            visitor.visit_any(loc, value)
