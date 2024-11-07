from typing import Annotated, Tuple, get_args
from modelity.invalid import Invalid
from modelity.interface import IModelConfig, IParser
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(Annotated)
def make_annotated_parser(tp: Annotated, model_config: IModelConfig):  # type: ignore

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
    type_parser = model_config.type_parser_provider.provide_type_parser(args[0], model_config)
    additional_parsers: Tuple[IParser, ...] = args[1:]
    return parse_annotated
