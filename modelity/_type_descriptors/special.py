from typing import cast, Annotated, Any, Iterator, Union, get_args

from modelity._registry import TypeDescriptorFactoryRegistry
from modelity.error import Error, ErrorFactory
from modelity.interface import IConstraint, IDumpFilter, ITypeDescriptor
from modelity.loc import Loc
from modelity.mixins import ExactDumpMixin
from modelity.unset import Unset

registry = TypeDescriptorFactoryRegistry()


@registry.type_descriptor_factory(Annotated)
def make_annotated_type_descriptor(typ, make_type_descriptor, type_opts) -> ITypeDescriptor:

    class AnnotatedTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = type_descriptor.parse(errors, loc, value)
            if result is Unset:
                return result
            for constraint in constraints:
                if not constraint(errors, loc, result):
                    return Unset
            return result

        def dump(self, loc: Loc, value: Any, filter: IDumpFilter):
            return type_descriptor.dump(loc, value, filter)

        def validate(self, root, ctx, errors, loc, value):
            for constraint in constraints:
                if not constraint(errors, loc, value):
                    return

    args = get_args(typ)
    type_descriptor: ITypeDescriptor = make_type_descriptor(args[0], type_opts)
    constraints = cast(Iterator[IConstraint], args[1:])
    return AnnotatedTypeDescriptor()


@registry.type_descriptor_factory(Union)
def make_union_type_descriptor(typ, make_type_descriptor, type_opts) -> ITypeDescriptor:

    class OptionalTypeDescriptor(ExactDumpMixin):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if value is None:
                return value
            return type_descriptor.parse(errors, loc, value)

        def validate(self, root, ctx, errors, loc, value):
            if value is not None:
                type_descriptor.validate(root, ctx, errors, loc, value)

    class UnionTypeDescriptor:
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

        def dump(self, loc: Loc, value: Any, filter: IDumpFilter):
            for typ, descriptor in zip(types, type_descriptors):
                if isinstance(value, typ):
                    return descriptor.dump(loc, value, filter)

        def validate(self, root, ctx, errors, loc, value):
            for typ, desc in zip(types, type_descriptors):
                if isinstance(value, typ):
                    desc.validate(root, ctx, errors, loc, value)

    types = get_args(typ)
    if len(types) == 2 and types[-1] is type(None):
        type_descriptor: ITypeDescriptor = make_type_descriptor(types[0], type_opts)
        return OptionalTypeDescriptor()
    type_descriptors: list[ITypeDescriptor] = [make_type_descriptor(typ, type_opts) for typ in types]
    return UnionTypeDescriptor()
