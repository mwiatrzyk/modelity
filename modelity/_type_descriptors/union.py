from typing import Any, get_args

from modelity.error import Error
from modelity.interface import IDumpFilter, ITypeDescriptor
from modelity.loc import Loc
from modelity.mixins import ExactDumpMixin
from modelity.unset import Unset


def make_union_type_descriptor(typ, **opts) -> ITypeDescriptor:

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
            errors.extend(inner_errors)
            return Unset

        def dump(self, loc: Loc, value: Any, filter: IDumpFilter):
            for typ, descriptor in zip(types, type_descriptors):
                if isinstance(value, typ):
                    return descriptor.dump(loc, value, filter)

        def validate(self, root, ctx, errors, loc, value):
            for typ, desc in zip(types, type_descriptors):
                if isinstance(value, typ):
                    desc.validate(root, ctx, errors, loc, value)

    from modelity._type_descriptors.main import make_type_descriptor

    types = get_args(typ)
    if len(types) == 2 and types[-1] is type(None):
        type_descriptor: ITypeDescriptor = make_type_descriptor(types[0], **opts)
        return OptionalTypeDescriptor()
    type_descriptors: list[ITypeDescriptor] = [make_type_descriptor(typ, **opts) for typ in types]
    return UnionTypeDescriptor()
