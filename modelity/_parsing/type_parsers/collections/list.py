import itertools
from typing import Iterable, Type, get_args

from modelity.error import ErrorCode, ErrorFactory
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.interface import IModelConfig
from modelity.providers import TypeParserProvider
from modelity._parsing.proxies import MutableSequenceProxy

provider = TypeParserProvider()


@provider.type_parser_factory(list)
def make_list_parser(tp: Type[list], model_config: IModelConfig):

    def parse_any_list(value, loc):
        if not isinstance(value, Iterable):
            return Invalid(value, ErrorFactory.create(loc, ErrorCode.ITERABLE_REQUIRED))
        return list(value)

    def parse_typed_list(value, loc):
        if not isinstance(value, Iterable):
            return Invalid(value, ErrorFactory.create(loc, ErrorCode.ITERABLE_REQUIRED))
        result = list(item_parser(x, loc + Loc(i)) for i, x in enumerate(value))
        errors = tuple(itertools.chain(*(x.errors for x in result if isinstance(x, Invalid))))
        if len(errors) > 0:
            return Invalid(value, *errors)
        return MutableSequenceProxy(result, loc, item_parser)

    args = get_args(tp)
    if len(args) == 0:
        return parse_any_list
    item_parser = model_config.type_parser_provider.provide_type_parser(args[0], model_config)
    return parse_typed_list
