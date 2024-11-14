from typing import List, Mapping, Type

from modelity.error import ErrorCode
from modelity.exc import ParsingError
from modelity.interface import IConfig, IError, IModel
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(IModel)
def make_model_parser(tp: Type[IModel]):

    def parse_model(value, loc, config: IConfig):
        if isinstance(value, tp):
            return value
        if not isinstance(value, Mapping):
            return Invalid(value, config.create_error(loc, ErrorCode.INVALID_MODEL, {"model_type": tp}))
        obj = tp()
        obj.set_config(config)
        obj.set_loc(loc)
        errors: List[IError] = []
        for k, v in value.items():
            try:
                setattr(obj, k, v)
            except ParsingError as e:
                errors.extend(e.errors)
        if errors:
            return Invalid(value, *errors)
        return obj

    return parse_model
