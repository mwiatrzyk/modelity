from typing import cast, Annotated, Any, Iterator, Union, get_args

from modelity._internal.registry import TypeDescriptorFactoryRegistry
from modelity.error import Error, ErrorFactory
from modelity.interface import IConstraint, IModelVisitor, ISupportsValidate, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset

registry = TypeDescriptorFactoryRegistry()


@registry.type_descriptor_factory(Annotated)
def make_annotated_type_descriptor(typ, make_type_descriptor, type_opts):

    class AnnotatedTypeDescriptor(ITypeDescriptor[Any], ISupportsValidate[Any]):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = type_descriptor.parse(errors, loc, value)
            if result is Unset:
                return result
            for constraint in constraints:
                if not constraint(errors, loc, result):
                    return Unset
            return result

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            if visitor.visit_supports_validate_begin(loc, value) is not True:
                type_descriptor.accept(visitor, loc, value)
                visitor.visit_supports_validate_end(loc, value)

        def validate(self, errors: list[Error], loc: Loc, value: Any):
            for constraint in constraints:
                if not constraint(errors, loc, value):
                    return

    args = get_args(typ)
    type_descriptor: ITypeDescriptor = make_type_descriptor(args[0], type_opts)
    constraints = cast(Iterator[IConstraint], args[1:])
    return AnnotatedTypeDescriptor()


@registry.type_descriptor_factory(Union)
def make_union_type_descriptor(typ, make_type_descriptor, type_opts) -> ITypeDescriptor:

    class OptionalTypeDescriptor(ITypeDescriptor[Any]):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if value is None:
                return value
            return type_descriptor.parse(errors, loc, value)

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            if value is None:
                return visitor.visit_none(loc, value)
            type_descriptor.accept(visitor, loc, value)

    class UnionTypeDescriptor(ITypeDescriptor[Any]):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            for t in types:
                if isinstance(value, t):
                    return value
            inner_errors: list[Error] = []
            for parser in type_descriptors:
                result = parser.parse(inner_errors, loc, value)
                if result is not Unset:
                    return result
            errors.append(ErrorFactory.union_parsing_error(loc, value, types))
            return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            for typ, descriptor in zip(types, type_descriptors):
                if isinstance(value, typ):
                    return descriptor.accept(visitor, loc, value)

    types = get_args(typ)
    if len(types) == 2 and types[-1] is type(None):
        type_descriptor: ITypeDescriptor = make_type_descriptor(types[0], type_opts)
        return OptionalTypeDescriptor()
    type_descriptors: list[ITypeDescriptor] = [make_type_descriptor(typ, type_opts) for typ in types]
    return UnionTypeDescriptor()
