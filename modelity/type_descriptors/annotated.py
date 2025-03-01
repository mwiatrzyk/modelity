from typing import Any, Iterator, cast, get_args

from modelity.error import Error
from modelity.interface import IConstraintCallable, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset


def make_annotated_type_descriptor(typ) -> ITypeDescriptor:
    """Make parser for the :class:`typing.Annotated` types.

    This parser assumes that the first argument of the annotated type is the
    type, and all remaining are :class:`IParser` protocol instances to be tried
    from left to right and only if type parsing was successful.

    :param typ:
        Type marked with :class:`typing.Annotated`, supplied with user-defined
        constraints.

        For example:

            ``Annotated[int, Gt(0), Lt(10)]``
    """

    class AnnotatedTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = type_descriptor.parse(errors, loc, value)
            if result is Unset:
                return result
            for constraint in constraints:
                if not constraint(errors, loc, result):
                    return Unset
            return result

        def accept(self, loc, value, visitor):
            type_descriptor.accept(loc, value, visitor)

    from modelity.type_descriptors.main import make_type_descriptor

    args = get_args(typ)
    type_descriptor = make_type_descriptor(args[0])
    constraints = cast(Iterator[IConstraintCallable], args[1:])
    return AnnotatedTypeDescriptor()
