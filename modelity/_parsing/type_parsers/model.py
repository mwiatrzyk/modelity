from typing import Mapping, Type

from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.interface import IModel
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(IModel)
def make_model_parser(tp: Type[IModel]):

    def parse_model(value, loc):
        if isinstance(value, tp):
            return value
        if not isinstance(value, Mapping):
            return Invalid(value, ErrorFactory.mapping_required(loc))
        try:
            obj = tp(**value)
            obj.set_loc(loc)
            return obj
        except ParsingError as e:
            errors = (Error(loc + e.loc, e.code, e.data) for e in e.errors)
            return Invalid(value, *errors)

    return parse_model
