from typing import Any, Mapping

from modelity._internal.registry import TypeDescriptorFactoryRegistry
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.interface import ITypeDescriptor
from modelity.model import Model
from modelity.unset import Unset

registry = TypeDescriptorFactoryRegistry()


@registry.type_descriptor_factory(Model)
def make_model_type_descriptor(typ: type[Model]) -> ITypeDescriptor:

    class ModelTypeDescriptor(ITypeDescriptor):

        def parse(self, errors, loc, value):
            if isinstance(value, typ):
                return value
            if not isinstance(value, Mapping):
                errors.append(ErrorFactory.invalid_type(loc, value, [typ], [Mapping]))
                return Unset
            try:
                return typ(**value)
            except ParsingError as e:
                errors.extend(Error(loc + x.loc, x.code, x.msg, x.value, x.data) for x in e.errors)
                return Unset

        def accept(self, visitor, loc, value):
            value.accept(visitor, loc)

    return ModelTypeDescriptor()
