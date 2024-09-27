import itertools
from typing import get_args
from modelity.error import Error, ErrorCode
from modelity.invalid import Invalid
from modelity.interface import ITypeParserProvider
from modelity.parsing.providers import TypeParserProvider
from modelity.parsing.types import MutableSetProxy

provider = TypeParserProvider()


@provider.type_parser_factory(set)
def make_set_parser(provider: ITypeParserProvider, tp: type):

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
    item_parser = provider.provide_type_parser(args[0])
    return parse_typed_set
