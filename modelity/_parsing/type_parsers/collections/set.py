import itertools
from typing import Iterable, Type, get_args

from modelity.error import ErrorCode
from modelity.invalid import Invalid
from modelity.interface import IConfig, IConfig
from modelity.providers import TypeParserProvider
from modelity._parsing.proxies import MutableSetProxy

provider = TypeParserProvider()


@provider.type_parser_factory(set)
def make_set_parser(tp: Type[set], model_config: IConfig):

    def ensure_iterable(value, loc, config: IConfig):
        if not isinstance(value, Iterable):
            return Invalid(value, config.create_error(loc, ErrorCode.ITERABLE_REQUIRED))
        return value

    def parse_any_set(value, loc, config: IConfig):
        result = ensure_iterable(value, loc, config)
        if isinstance(result, Invalid):
            return result
        try:
            return set(result)
        except TypeError:
            return Invalid(value, config.create_error(loc, ErrorCode.HASHABLE_REQUIRED))

    def parse_typed_set(value, loc, config: IConfig):
        result = ensure_iterable(value, loc, config)
        if isinstance(result, Invalid):
            return result
        try:
            result = set(item_parser(x, loc, config) for x in result)
        except TypeError:
            return Invalid(value, config.create_error(loc, ErrorCode.HASHABLE_REQUIRED))
        errors = tuple(itertools.chain(*(x.errors for x in result if isinstance(x, Invalid))))
        if len(errors) > 0:
            return Invalid(value, *errors)
        return MutableSetProxy(result, loc, config, item_parser)

    args = get_args(tp)
    if not args:
        return parse_any_set
    item_parser = model_config.type_parser_provider.provide_type_parser(args[0], model_config)
    return parse_typed_set
