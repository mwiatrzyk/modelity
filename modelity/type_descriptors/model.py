from typing import Mapping

from modelity.error import Error, ErrorFactory
from modelity.exc import ModelParsingError
from modelity.interface import IDumpFilter, IModel, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset


def make_model_type_descriptor(typ: type) -> ITypeDescriptor:
    """Make type descriptor for any subclass of the
    :class:`modelity.model.Model` class.

    :param typ:
        Model type.
    """

    class ModelTypeDescriptor:

        def parse(self, errors: list[Error], loc: Loc, value: IModel):
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

        def dump(self, loc: Loc, value: IModel, filter: IDumpFilter):
            return value.dump(loc, filter)

        def validate(self, root, ctx, errors, loc, value: IModel):
            value.validate(root, ctx, errors, loc)

    return ModelTypeDescriptor()
