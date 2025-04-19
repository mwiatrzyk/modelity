from typing import Mapping

from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.interface import IDumpFilter, IModel, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset


def make_model_type_descriptor(typ: type[IModel]) -> ITypeDescriptor:

    class ModelTypeDescriptor:

        def parse(self, errors: list[Error], loc: Loc, value: IModel):
            if isinstance(value, typ):
                value.__loc__ = loc
                return value
            if not isinstance(value, Mapping):
                errors.append(ErrorFactory.invalid_model(loc, value, typ))
                return Unset
            try:
                obj = typ(**value)
                obj.__loc__ = loc
                return obj
            except ParsingError as e:
                errors.extend(Error(loc + x.loc, x.code, x.msg, x.value, x.data) for x in e.errors)
                return Unset

        def dump(self, loc: Loc, value: IModel, filter: IDumpFilter):
            return value.dump(filter)

        def validate(self, root, ctx, errors, loc, value: IModel):
            value.validate(root, ctx, errors)

    return ModelTypeDescriptor()
