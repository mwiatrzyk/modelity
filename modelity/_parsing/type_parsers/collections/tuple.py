import itertools
from typing import Type, get_args

from modelity.error import ErrorCode, ErrorFactory
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.interface import IModelConfig
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(tuple)
def make_tuple_parser(tp: Type[tuple], model_config: IModelConfig):

    def parse_any_tuple(value, loc):
        try:
            return tuple(value)
        except TypeError:
            return Invalid(value, ErrorFactory.create(loc, ErrorCode.ITERABLE_REQUIRED))

    def parse_any_length_typed_tuple(value, loc):
        result = parse_any_tuple(value, loc)
        if isinstance(result, Invalid):
            return result
        result = tuple(parser(x, loc + Loc(pos)) for pos, x in enumerate(result))
        errors = tuple(itertools.chain(*(x.errors for x in result if isinstance(x, Invalid))))
        if len(errors) > 0:
            return Invalid(value, *errors)
        return result

    def parse_fixed_length_typed_tuple(value, loc):
        result = parse_any_tuple(value, loc)
        if isinstance(result, Invalid):
            return result
        result = tuple(parse(elem, loc + Loc(i)) for i, parse, elem in zip(range(len(result)), parsers, result))
        if len(result) != len(args):
            return Invalid(value, ErrorFactory.create_invalid_tuple_format(loc, args))
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
