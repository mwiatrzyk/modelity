import itertools
from typing import Iterable, get_args

from modelity.error import Error, ErrorCode
from modelity.invalid import Invalid
from modelity.parsing.interface import IParserRegistry
from modelity.parsing.registry import TypeParserRegistry
from modelity.parsing.types import MutableSequenceProxy

registry = TypeParserRegistry()


@registry.type_parser_factory(list)
def make_list_parser(registry: IParserRegistry, tp: type):

    def parse_any_list(value, loc):
        if not isinstance(value, Iterable):
            return Invalid(value, Error.create(loc, ErrorCode.ITERABLE_REQUIRED))
        return list(value)

    def parse_typed_list(value, loc):
        if not isinstance(value, Iterable):
            return Invalid(value, Error.create(loc, ErrorCode.ITERABLE_REQUIRED))
        result = list(item_parser(x, loc + (i,)) for i, x in enumerate(value))
        errors = tuple(itertools.chain(*(x.errors for x in result if isinstance(x, Invalid))))
        if len(errors) > 0:
            return Invalid(value, *errors)
        return MutableSequenceProxy(result, loc, item_parser)

    args = get_args(tp)
    if len(args) == 0:
        return parse_any_list
    item_parser = registry.require_parser(args[0])
    return parse_typed_list
