import itertools
from typing import Iterable, get_args

from modelity.error import Error, ErrorCode
from modelity.invalid import Invalid
from modelity.interface import ITypeParserProvider
from modelity.providers import TypeParserProvider
from modelity._parsing.proxies import MutableSetProxy

provider = TypeParserProvider()


@provider.type_parser_factory(set)
def make_set_parser(provider: ITypeParserProvider, tp: type):

    def ensure_iterable(value, loc):
        if not isinstance(value, Iterable):
            return Invalid(value, Error.create(loc, ErrorCode.ITERABLE_REQUIRED))
        return value

    def parse_any_set(value, loc):
        result = ensure_iterable(value, loc)
        if isinstance(result, Invalid):
            return result
        try:
            return set(result)
        except TypeError:
            return Invalid(value, Error.create(loc, ErrorCode.HASHABLE_REQUIRED))

    def parse_typed_set(value, loc):
        result = ensure_iterable(value, loc)
        if isinstance(result, Invalid):
            return result
        try:
            result = set(item_parser(x, loc) for x in result)
        except TypeError:
            return Invalid(value, Error.create(loc, ErrorCode.HASHABLE_REQUIRED))
        errors = tuple(itertools.chain(*(x.errors for x in result if isinstance(x, Invalid))))
        if len(errors) > 0:
            return Invalid(value, *errors)
        return MutableSetProxy(result, loc, item_parser)

    args = get_args(tp)
    if not args:
        return parse_any_set
    item_parser = provider.provide_type_parser(args[0])
    return parse_typed_set
