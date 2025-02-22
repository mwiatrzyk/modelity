from typing import Any, Union, get_args, get_origin

from modelity.error import Error, ErrorFactory
from modelity.interface import IParser
from modelity.loc import Loc
from modelity.unset import Unset


def make_union_parser(typ, **opts) -> IParser:
    """Make parser for the :class:`typing.Union` type.

    :param typ:
        The union type to create parser for.
    """
    from modelity.parsing.main import make_parser

    def parse_optional(errors: list[Error], loc: Loc, value: Any):
        if value is None:
            return value
        return parser(errors, loc, value)

    def parse_union(errors: list[Error], loc: Loc, value: Any):
        for t in types:
            if isinstance(value, t):
                return value
        local_errors = []
        for parser in type_parsers:
            result = parser(local_errors, loc, value)
            if result is not Unset:
                return result
        errors.extend(local_errors)
        errors.append(ErrorFactory.union_parsing_failed(loc, value, types))
        return Unset

    origin = get_origin(typ)
    assert origin is Union, f"{make_union_parser.__name__!r} can only be used with unions"
    types = get_args(typ)
    if len(types) == 2 and types[-1] is type(None):
        parser = make_parser(types[0], **opts)
        return parse_optional
    type_parsers = [make_parser(typ, **opts) for typ in types]
    return parse_union
