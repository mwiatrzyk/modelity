import itertools
from typing import Type, get_args

from modelity.error import ErrorCode
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.interface import IConfig, IConfig
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(tuple)
def make_tuple_parser(tp: Type[tuple], model_config: IConfig):

    def parse_any_tuple(value, loc, config: IConfig):
        try:
            return tuple(value)
        except TypeError:
            return Invalid(value, config.create_error(loc, ErrorCode.ITERABLE_REQUIRED))

    def parse_any_length_typed_tuple(value, loc, config):
        result = parse_any_tuple(value, loc, config)
        if isinstance(result, Invalid):
            return result
        result = tuple(parser(x, loc + Loc(pos), config) for pos, x in enumerate(result))
        errors = tuple(itertools.chain(*(x.errors for x in result if isinstance(x, Invalid))))
        if len(errors) > 0:
            return Invalid(value, *errors)
        return result

    def parse_fixed_length_typed_tuple(value, loc, config: IConfig):
        result = parse_any_tuple(value, loc, config)
        if isinstance(result, Invalid):
            return result
        result = tuple(parse(elem, loc + Loc(i), config) for i, parse, elem in zip(range(len(result)), parsers, result))
        if len(result) != len(args):
            return Invalid(value, config.create_error(loc, ErrorCode.INVALID_TUPLE_FORMAT, {"expected_format": args}))
        errors = tuple(itertools.chain(*(x.errors for x in result if isinstance(x, Invalid))))
        if len(errors) > 0:
            return Invalid(value, *errors)
        return result

    args = get_args(tp)
    if not args:
        return parse_any_tuple
    provide_type_parser = model_config.type_parser_provider.provide_type_parser
    if args[-1] is Ellipsis:
        parser = provide_type_parser(args[0], model_config)
        return parse_any_length_typed_tuple
    parsers = tuple(provide_type_parser(x, model_config) for x in args)
    return parse_fixed_length_typed_tuple
