from datetime import datetime
from enum import Enum
from numbers import Number
from typing import Annotated, Any, Literal, Type, TypeVar, Union, get_origin

from modelity.exc import UnsupportedTypeError
from modelity.interface import IParser
from modelity.parsing.annotated import make_annotated_parser
from modelity.parsing.simple import (
    make_any_parser,
    make_bool_parser,
    make_bytes_parser,
    make_datetime_parser,
    make_enum_parser,
    make_literal_parser,
    make_none_parser,
    make_number_parser,
    make_str_parser,
)
from modelity.parsing.union import make_union_parser
from modelity.parsing.collections import make_dict_parser, make_list_parser, make_set_parser, make_tuple_parser

T = TypeVar("T")


def make_parser(typ: Union[Type[T], Any], **opts) -> IParser[T]:
    """Central parser making function.

    Creates parser for any of the built-in type given via *typ* argument or
    raises :exc:`modelity.exc.UnsupportedTypeError` if there was no parser
    found for the given type.

    :param typ:
        The type to create parser for.

    :param `**opts`:
        Parser factory options.
    """
    if typ is Any:
        return make_any_parser()
    if typ is type(None):
        return make_none_parser()
    origin = get_origin(typ)
    if origin is Literal:
        return make_literal_parser(typ)
    if origin is Annotated:
        return make_annotated_parser(typ)
    if origin is Union:
        return make_union_parser(typ, **opts)
    if origin is tuple:
        return make_tuple_parser(typ, **opts)
    if origin is dict:
        return make_dict_parser(typ, **opts)
    if origin is list:
        return make_list_parser(typ, **opts)
    if origin is set:
        return make_set_parser(typ, **opts)
    if issubclass(typ, bool):
        return make_bool_parser(**opts)
    if issubclass(typ, datetime):
        return make_datetime_parser(**opts)
    if issubclass(typ, str):
        return make_str_parser(**opts)
    if issubclass(typ, bytes):
        return make_bytes_parser(**opts)
    if issubclass(typ, Enum):
        return make_enum_parser(typ)
    if issubclass(typ, Number):
        return make_number_parser(typ)
    if issubclass(typ, tuple):
        return make_tuple_parser(typ, **opts)
    if issubclass(typ, dict):
        return make_dict_parser(typ, **opts)
    if issubclass(typ, list):
        return make_list_parser(typ, **opts)
    if issubclass(typ, set):
        return make_set_parser(typ, **opts)
    raise UnsupportedTypeError(typ)
