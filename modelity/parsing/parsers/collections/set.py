import itertools
from typing import get_args
from modelity.error import Error, ErrorCode
from modelity.invalid import Invalid
from modelity.parsing.interface import IParserRegistry
from modelity.parsing.registry import TypeParserRegistry
from modelity.parsing.types import MutableSetProxy

registry = TypeParserRegistry()


@registry.type_parser_factory(set)
def make_set_parser(registry: IParserRegistry, tp: type):

    def parse_any_set(value, loc):
        try:
            return set(value)
        except TypeError:
            return Invalid(value, Error.create(loc, ErrorCode.ITERABLE_REQUIRED))

    def parse_typed_set(value, loc):
        result = parse_any_set(value, loc)
        if isinstance(result, Invalid):
            return result
        result = set(item_parser(x, loc) for x in value)
        errors = tuple(itertools.chain(*(x.errors for x in result if isinstance(x, Invalid))))
        if len(errors) > 0:
            return Invalid(value, *errors)
        return MutableSetProxy(result, loc, item_parser)

    args = get_args(tp)
    if not args:
        return parse_any_set
    item_parser = registry.require_parser(args[0])
    return parse_typed_set