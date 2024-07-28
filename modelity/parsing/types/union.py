from typing import Type, Union, get_args

from modelity.exc import ParsingError
from modelity.parsing.interface import IParserRegistry
from modelity.parsing.registry import ParserRegistry

registry = ParserRegistry()


@registry.type_parser_factory(Union)
def make_union_parser(root_parser_registry: IParserRegistry, tp: Type):

    def parse_union(value):
        for parser in parsers:
            try:
                return parser(value)
            except ParsingError:
                pass
        raise ParsingError(f"Unsupported type of input value; supported ones are: {', '.join(repr(x) for x in args)}")

    args = get_args(tp)
    parsers = [root_parser_registry.require_parser(x) for x in args]
    return parse_union
