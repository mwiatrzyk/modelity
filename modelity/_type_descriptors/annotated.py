from typing import Annotated, Any, Iterator, TypeVar, cast, get_args

from modelity.error import Error
from modelity.interface import IConstraint, IDumpFilter, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset


def make_annotated_type_descriptor(typ: Any, **opts: Any) -> ITypeDescriptor:

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

    from modelity._type_descriptors.main import make_type_descriptor

    args = get_args(typ)
    type_descriptor: ITypeDescriptor = make_type_descriptor(args[0], **opts)
    constraints = cast(Iterator[IConstraint], args[1:])
    return AnnotatedTypeDescriptor()
