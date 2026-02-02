from typing import cast, Annotated, Any, Iterator, Union, get_args

from modelity._internal.registry import TypeDescriptorFactoryRegistry
from modelity.error import Error, ErrorFactory
from modelity.interface import IConstraint, IModelVisitor, IValidatableTypeDescriptor, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType

registry = TypeDescriptorFactoryRegistry()


@registry.type_descriptor_factory(Annotated)
def make_annotated_type_descriptor(typ, make_type_descriptor, type_opts):

    class AnnotatedTypeDescriptor(IValidatableTypeDescriptor):
        def parse(self, errors, loc, value):
            result = type_descriptor.parse(errors, loc, value)
            if result is Unset:
                return result
            for constraint in constraints:
                if not constraint(errors, loc, result):
                    return Unset
            return result

        def accept(self, visitor, loc, value):
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

    class OptionalTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            if value is None:
                return value
            return type_descriptor.parse(errors, loc, value)

        def accept(self, visitor, loc, value):
            if value is None:
                return visitor.visit_none(loc, value)
            type_descriptor.accept(visitor, loc, value)

    class StrictOptionalTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
            if value is Unset:
                return value
            if value is None:
                errors.append(ErrorFactory.none_not_allowed(loc, typ))
                return Unset
            return type_descriptor.parse(errors, loc, value)

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            if value is Unset:
                return visitor.visit_unset(loc, value)
            return type_descriptor.accept(visitor, loc, value)

    class UnionTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            for t in types:
                if isinstance(value, t):
                    return value
            inner_errors: list[Error] = []
            for parser in type_descriptors:
                result = parser.parse(inner_errors, loc, value)
                if result is not Unset:
                    return result
            errors.append(ErrorFactory.invalid_type(loc, value, list(types)))
            return Unset

        def accept(self, visitor, loc, value):
            for typ, descriptor in zip(types, type_descriptors):
                if isinstance(value, typ):
                    return descriptor.accept(visitor, loc, value)

    types = get_args(typ)
    if len(types) == 2:
        type_descriptor: ITypeDescriptor = make_type_descriptor(types[0], type_opts)
        if types[-1] is type(None):
            return OptionalTypeDescriptor()
        elif types[-1] is UnsetType:
            return StrictOptionalTypeDescriptor()
    type_descriptors: list[ITypeDescriptor] = [make_type_descriptor(typ, type_opts) for typ in types]
    return UnionTypeDescriptor()
