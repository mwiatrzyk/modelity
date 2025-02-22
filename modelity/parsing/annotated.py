from typing import Annotated, Any, cast, get_args, get_origin

from modelity.error import Error
from modelity.interface import IParser
from modelity.loc import Loc
from modelity.unset import Unset


def make_annotated_parser(typ) -> IParser:
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

    def parse_annotated(errors: list[Error], loc: Loc, value: Any):
        result = parse_type(errors, loc, value)
        if result is Unset:
            return result
        for constraint in constraints:
            result = constraint(errors, loc, result)
            if result is Unset:
                return result
        return result

    from modelity.parsing.main import make_parser

    origin = get_origin(typ)
    assert origin is Annotated, f"{make_annotated_parser.__name__!r} can only be used with annotated types"
    args = get_args(typ)
    parse_type = make_parser(args[0])
    constraints = cast(tuple[IParser], args[1:])
    return parse_annotated
