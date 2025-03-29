from typing import Annotated, Any, Iterator, TypeVar, cast, get_args

from modelity.error import Error
from modelity.interface import IConstraintCallable, IDumpFilter, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset


def make_annotated_type_descriptor(typ: Any, **opts: Any) -> ITypeDescriptor:
    """Make descriptor for type created using :class:`typing.Annotated` object.

    For example, this function will create descriptor for constrained integer
    type, like in this example:

    .. testcode::

        from typing import Annotated
        from modelity.constraints import Gt

        PositiveInteger = Annotated[int, Gt(0)]

    :param typ:
        The type to create descriptor for.

    :param `**opts`:
        Options to be passed to the inner type descriptor.
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

        def dump(self, loc: Loc, value: Any, filter: IDumpFilter):
            return type_descriptor.dump(loc, value, filter)

        def validate(self, root, ctx, errors, loc, value):
            for constraint in constraints:
                if not constraint(errors, loc, value):
                    return

    from modelity.type_descriptors.main import make_type_descriptor

    args = get_args(typ)
    type_descriptor = make_type_descriptor(args[0], **opts)
    constraints = cast(Iterator[IConstraintCallable], args[1:])
    return AnnotatedTypeDescriptor()
