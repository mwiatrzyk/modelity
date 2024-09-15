from typing import Mapping

from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.interface import IModel
from modelity.invalid import Invalid
from modelity.parsing.registry import TypeParserRegistry

registry = TypeParserRegistry()


@registry.type_parser_factory(IModel)
def make_model_parser(tp: IModel):

    def parse_model(value, loc):
        if isinstance(value, tp):
            return value
        if not isinstance(value, Mapping):
            return Invalid(value, ErrorFactory.mapping_required(loc))
        try:
            return tp(**value)
        except ParsingError as e:
            errors = (Error(loc + e.loc, e.code, e.data) for e in e.errors)
            return Invalid(value, *errors)

    return parse_model
