import itertools
from typing import get_args

from modelity.error import Error, ErrorCode
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.interface import ITypeParserProvider
from modelity.providers import TypeParserProvider
from modelity._parsing.proxies import MutableMappingProxy

provider = TypeParserProvider()


@provider.type_parser_factory(dict)
def make_dict_parser(provider: ITypeParserProvider, tp: type):

    def parse_dict(value, loc):
        try:
            return dict(value)
        except TypeError:
            return Invalid(value, Error.create(loc, ErrorCode.MAPPING_REQUIRED))

    def parse_typed_dict(value, loc):
        result = parse_dict(value, loc)
        if isinstance(result, Invalid):
            return result
        result = dict((key_parser(k, loc), value_parser(v, loc + Loc(k))) for k, v in result.items())
        value_errors = itertools.chain(*(x.errors for x in result.values() if isinstance(x, Invalid)))
        key_errors = itertools.chain(*(x.errors for x in result.keys() if isinstance(x, Invalid)))
        errors = tuple(itertools.chain(key_errors, value_errors))
        if len(errors) > 0:
            return Invalid(value, *errors)
        return MutableMappingProxy(result, loc, key_parser, value_parser)

    args = get_args(tp)
    if not args:
        return parse_dict
    key_type, value_type = args
    key_parser = provider.provide_type_parser(key_type)
    value_parser = provider.provide_type_parser(value_type)
    return parse_typed_dict
