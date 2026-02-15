from typing import Literal, Sequence, cast, Annotated, Any, Iterator, Union, get_args

from modelity._internal.registry import TypeDescriptorFactoryRegistry
from modelity.error import Error, ErrorFactory
from modelity.interface import IConstraint, IModelVisitor, IValidatableTypeDescriptor, ITypeDescriptor
from modelity.loc import Loc
from modelity.types import is_deferred
from modelity.unset import Unset, UnsetType

registry = TypeDescriptorFactoryRegistry()


class _OptionalTypeDescriptor(ITypeDescriptor):

    def __init__(self, type_descriptor: ITypeDescriptor):
        self._type_descriptor = type_descriptor

    def parse(self, errors, loc, value):
        if value is None:
            return value
        return self._type_descriptor.parse(errors, loc, value)

    def accept(self, visitor, loc, value):
        if value is None:
            return visitor.visit_none(loc, value)
        self._type_descriptor.accept(visitor, loc, value)


class _UnionTypeDescriptor(ITypeDescriptor):

    def __init__(self, types: tuple[Any, ...], type_descriptors: list[ITypeDescriptor]):
        self._types = types
        self._type_descriptors = type_descriptors

    def parse(self, errors, loc, value):
        for t in self._types:
            if isinstance(value, t):
                return value
        inner_errors: list[Error] = []
        for parser in self._type_descriptors:
            result = parser.parse(inner_errors, loc, value)
            if result is not Unset:
                return result
        errors.append(ErrorFactory.invalid_type(loc, value, list(self._types)))
        return Unset

    def accept(self, visitor, loc, value):
        for typ, descriptor in zip(self._types, self._type_descriptors):
            if isinstance(value, typ):
                return descriptor.accept(visitor, loc, value)


@registry.type_descriptor_factory(Annotated)
def make_annotated_type_descriptor(typ, make_type_descriptor, type_opts):

    class AnnotatedTypeDescriptor(IValidatableTypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = type_descriptor.parse(errors, loc, value)
            if result is Unset:
                return result
            for constraint in constraints:
                if not constraint(errors, loc, result):
                    return Unset
            return result

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            type_descriptor.accept(visitor, loc, value)

        def validate(self, errors: list[Error], loc: Loc, value: Any):
            for constraint in constraints:
                if not constraint(errors, loc, value):
                    return

    if is_deferred(typ):
        args = get_args(typ)
        types = tuple(x for x in get_args(args[0]) if x is not UnsetType)
        if len(types) == 1:
            return make_type_descriptor(types[0], type_opts)
        elif len(types) == 2 and types[-1] is type(None):
            return _OptionalTypeDescriptor(make_type_descriptor(types[0], type_opts))
        type_descriptors = [make_type_descriptor(x, type_opts) for x in types]
        return _UnionTypeDescriptor(types, type_descriptors)
    args = get_args(typ)
    type_descriptor: ITypeDescriptor = make_type_descriptor(args[0], type_opts)
    constraints = cast(Sequence[IConstraint], args[1:])
    return AnnotatedTypeDescriptor()


@registry.type_descriptor_factory(Union)
def make_union_type_descriptor(typ, make_type_descriptor, type_opts) -> ITypeDescriptor:

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

    types = get_args(typ)
    if len(types) == 2:
        type_descriptor: ITypeDescriptor = make_type_descriptor(types[0], type_opts)
        if types[-1] is type(None):
            return _OptionalTypeDescriptor(type_descriptor)
        elif types[-1] is UnsetType:
            return StrictOptionalTypeDescriptor()
    type_descriptors: list[ITypeDescriptor] = [make_type_descriptor(typ, type_opts) for typ in types]
    return _UnionTypeDescriptor(types, type_descriptors)
