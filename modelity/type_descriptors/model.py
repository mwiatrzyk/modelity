from typing import Any, Mapping

from modelity.error import Error, ErrorFactory
from modelity.exc import ModelParsingError
from modelity.interface import IModelVisitor, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset


def make_model_type_descriptor(typ: type) -> ITypeDescriptor:
    """Make type descriptor for any subclass of the
    :class:`modelity.model.Model` class.

    :param typ:
        Model type.
    """
    from modelity.model import Model

    class ModelTypeDescriptor:

        def parse(self, errors: list[Error], loc: Loc, value: Model):
            if isinstance(value, typ):
                return value
            if not isinstance(value, Mapping):
                errors.append(ErrorFactory.invalid_model(loc, value, typ))
                return Unset
            try:
                obj = typ(**value)
            except ModelParsingError as e:
                errors.extend(Error(loc + x.loc, x.code, x.msg, x.value, x.data) for x in e.errors)
            else:
                return obj

        def accept(self, loc: Loc, value: Model, visitor: IModelVisitor):
            visitor.visit_model_begin(loc, value)
            value.accept(loc, visitor)
            visitor.visit_model_end(loc, value)

        def validate(self, errors: list[Error], loc: Loc, value: Model):
            return value.validate(None, errors, loc)

    return ModelTypeDescriptor()
