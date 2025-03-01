from datetime import datetime
from enum import Enum
from numbers import Number
from typing import Annotated, Any, Literal, Type, TypeVar, Union, get_origin

from modelity.exc import UnsupportedTypeError
from modelity.interface import ITypeDescriptor

from .any import make_any_type_descriptor
from .model import make_model_type_descriptor
from .annotated import make_annotated_type_descriptor
from .simple import (
    make_bool_type_descriptor,
    make_bytes_type_descriptor,
    make_datetime_type_descriptor,
    make_enum_type_descriptor,
    make_literal_type_descriptor,
    make_none_type_descriptor,
    make_numeric_type_descriptor,
    make_str_type_descriptor,
)
from .union import make_union_type_descriptor
from .collections import (
    make_dict_type_descriptor,
    make_list_type_descriptor,
    make_set_type_descriptor,
    make_tuple_type_descriptor,
)

T = TypeVar("T")


def make_type_descriptor(typ: Union[Type[T], Any], **opts) -> ITypeDescriptor[T]:
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
        return make_any_type_descriptor()
    if typ is type(None):
        return make_none_type_descriptor()
    origin = get_origin(typ)
    if origin is Literal:
        return make_literal_type_descriptor(typ)
    if origin is Annotated:
        return make_annotated_type_descriptor(typ)
    if origin is Union:
        return make_union_type_descriptor(typ, **opts)
    if origin is tuple:
        return make_tuple_type_descriptor(typ, **opts)
    if origin is dict:
        return make_dict_type_descriptor(typ, **opts)
    if origin is list:
        return make_list_type_descriptor(typ, **opts)
    if origin is set:
        return make_set_type_descriptor(typ, **opts)
    if issubclass(typ, bool):
        return make_bool_type_descriptor(**opts)
    if issubclass(typ, datetime):
        return make_datetime_type_descriptor(**opts)
    if issubclass(typ, str):
        return make_str_type_descriptor(**opts)
    if issubclass(typ, bytes):
        return make_bytes_type_descriptor(**opts)
    if issubclass(typ, Enum):
        return make_enum_type_descriptor(typ)
    if issubclass(typ, Number):
        return make_numeric_type_descriptor(typ)
    if issubclass(typ, tuple):
        return make_tuple_type_descriptor(typ, **opts)
    if issubclass(typ, dict):
        return make_dict_type_descriptor(typ, **opts)
    if issubclass(typ, list):
        return make_list_type_descriptor(typ, **opts)
    if issubclass(typ, set):
        return make_set_type_descriptor(typ, **opts)
    from modelity.model import Model

    if issubclass(typ, Model):
        return make_model_type_descriptor(typ, **opts)
    raise UnsupportedTypeError(typ)
