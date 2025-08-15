from typing import Any, Mapping

from modelity._internal.registry import TypeDescriptorFactoryRegistry
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.interface import IModel, IModelVisitor, ITypeDescriptor
from modelity.loc import Loc
from modelity.model import Model
from modelity.unset import Unset

registry = TypeDescriptorFactoryRegistry()


@registry.type_descriptor_factory(Model)
def make_model_type_descriptor(typ: type[IModel]) -> ITypeDescriptor:

    class ModelTypeDescriptor(ITypeDescriptor[IModel]):

        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, typ):
                return value
            if not isinstance(value, Mapping):
                errors.append(ErrorFactory.model_parsing_error(loc, value, typ))
                return Unset
            try:
                return typ(**value)
            except ParsingError as e:
                errors.extend(Error(loc + x.loc, x.code, x.msg, x.value, x.data) for x in e.errors)

        def accept(self, visitor: IModelVisitor, loc: Loc, value: IModel):
            value.accept(visitor, loc)

    return ModelTypeDescriptor()
