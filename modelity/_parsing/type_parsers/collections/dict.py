import itertools
from typing import Type, get_args

from modelity.error import ErrorCode
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.interface import IConfig, IConfig
from modelity.providers import TypeParserProvider
from modelity._parsing.proxies import MutableMappingProxy

provider = TypeParserProvider()


@provider.type_parser_factory(dict)
def make_dict_parser(tp: Type[dict], model_config: IConfig):

    def parse_dict(value, loc, config: IConfig):
        try:
            return dict(value)
        except TypeError:
            return Invalid(value, config.create_error(loc, ErrorCode.MAPPING_REQUIRED))

    def parse_typed_dict(value, loc, config):
        result = parse_dict(value, loc, config)
        if isinstance(result, Invalid):
            return result
        result = dict((key_parser(k, loc, config), value_parser(v, loc + Loc(k), config)) for k, v in result.items())
        value_errors = itertools.chain(*(x.errors for x in result.values() if isinstance(x, Invalid)))
        key_errors = itertools.chain(*(x.errors for x in result.keys() if isinstance(x, Invalid)))
        errors = tuple(itertools.chain(key_errors, value_errors))
        if len(errors) > 0:
            return Invalid(value, *errors)
        return MutableMappingProxy(result, loc, config, key_parser, value_parser)

    args = get_args(tp)
    if not args:
        return parse_dict
    key_type, value_type = args
    key_parser = model_config.type_parser_provider.provide_type_parser(key_type, model_config)
    value_parser = model_config.type_parser_provider.provide_type_parser(value_type, model_config)
    return parse_typed_dict
