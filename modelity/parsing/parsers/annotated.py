from typing import Annotated, Tuple, get_args
from modelity.invalid import Invalid
from modelity.parsing.interface import IParser, IParserRegistry
from modelity.parsing.registry import TypeParserRegistry

registry = TypeParserRegistry()


@registry.type_parser_factory(Annotated)
def make_annotated_parser(registry: IParserRegistry, tp: Annotated):

    def parse_annotated(value, loc):
        result = type_parser(value, loc)
        if isinstance(result, Invalid):
            return result
        for parser in additional_parsers:
            result = parser(result, loc)
            if isinstance(result, Invalid):
                return result
        return result

    args = get_args(tp)
    assert len(args) >= 2
    type_parser = registry.require_parser(args[0])
    additional_parsers: Tuple[IParser, ...] = args[1:]
    return parse_annotated
