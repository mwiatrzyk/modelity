import collections.abc
import datetime
import enum
import ipaddress
import pathlib
from typing import Annotated, Any, Literal, MutableSequence, Union, get_origin

from modelity import _utils
from modelity.base import TypeHandler, Model, TypeHandlerFactory
from modelity.exc import UnsupportedTypeError
from modelity.unset import UnsetType

from .type_handlers.any import AnyTypeHandler
from .type_handlers.mapping import create_mutable_mapping_type_handler
from .type_handlers.model import ModelTypeHandler
from .type_handlers.none import NoneTypeHandler
from .type_handlers.scalar import (
    BoolTypeHandler,
    BytesTypeHandler,
    DateTimeTypeHandler,
    DateTypeHandler,
    EnumTypeHandler,
    IPAddressTypeHandler,
    LiteralTypeHandler,
    NumericTypeHandler,
    PathTypeHandler,
    StrTypeHandler,
)
from .type_handlers.sequence import create_mutable_sequence_type_handler, create_sequence_type_handler
from .type_handlers.set import create_mutable_set_type_handler
from .type_handlers.special import create_annotated_type_handler, create_union_type_handler
from .type_handlers.unset import UnsetTypeHandler

_DEFAULT_EXPECTED_DATETIME_FORMATS = [
    "YYYY-MM-DDThh:mm:ssZZZZ",
    "YYYY-MM-DDThh:mm:ss.ffffffZZZZ",
    "YYYY-MM-DDThh:mm:ss",
    "YYYY-MM-DDThh:mm:ss.ffffff",
    "YYYY-MM-DD hh:mm:ss ZZZZ",
    "YYYY-MM-DD hh:mm:ss.ffffff ZZZZ",
    "YYYY-MM-DD hh:mm:ss",
    "YYYY-MM-DD hh:mm:ss.ffffff",
    "YYYYMMDDThhmmssZZZZ",
    "YYYYMMDDThhmmss.ffffffZZZZ",
    "YYYYMMDDThhmmss",
    "YYYYMMDDThhmmss.ffffff",
    "YYYYMMDDhhmmssZZZZ",
    "YYYYMMDDhhmmss.ffffffZZZZ",
    "YYYYMMDDhhmmss",
    "YYYYMMDDhhmmss.ffffff",
]

_DEFAULT_EXPECTED_DATE_FORMATS = ["YYYY-MM-DD"]

_type_handler_map = {
    # type_handlers/any.py
    # --------------------
    Any: lambda typ, type_opts: AnyTypeHandler(),
    # type_handlers/none.py
    # ---------------------
    type(None): lambda typ, type_opts: NoneTypeHandler(),
    # type_handlers/scalar.py
    # -----------------------
    bool: lambda typ, type_opts: BoolTypeHandler(**type_opts),
    datetime.datetime: lambda typ, type_opts: DateTimeTypeHandler(
        **_utils.with_defaults(type_opts, expected_datetime_formats=_DEFAULT_EXPECTED_DATETIME_FORMATS)
    ),
    datetime.date: lambda typ, type_opts: DateTypeHandler(
        **_utils.with_defaults(type_opts, expected_date_formats=_DEFAULT_EXPECTED_DATE_FORMATS)
    ),
    enum.Enum: lambda typ, type_opts: EnumTypeHandler(typ),
    Literal: lambda typ, type_opts: LiteralTypeHandler(typ),
    int: lambda typ, type_opts: NumericTypeHandler(typ),
    float: lambda typ, type_opts: NumericTypeHandler(typ),
    str: lambda typ, type_opts: StrTypeHandler(),
    bytes: lambda typ, type_opts: BytesTypeHandler(),
    ipaddress.IPv4Address: lambda typ, type_opts: IPAddressTypeHandler(typ),
    ipaddress.IPv6Address: lambda typ, type_opts: IPAddressTypeHandler(typ),
    pathlib.Path: lambda typ, type_opts: PathTypeHandler(),
    # type_handlers/unset.py
    # ----------------------
    UnsetType: lambda typ, type_opts: UnsetTypeHandler(),
    # type_handlers/model.py
    # ----------------------
    Model: lambda typ, type_opts: ModelTypeHandler(typ),
    # type_handlers/mapping.py
    # ------------------------
    dict: lambda typ, type_opts: create_mutable_mapping_type_handler(typ, create_type_handler, **type_opts),
    collections.abc.MutableMapping: lambda typ, type_opts: create_mutable_mapping_type_handler(
        typ, create_type_handler, **type_opts
    ),
    # type_handlers/sequence.py
    # -------------------------
    list: lambda typ, type_opts: create_mutable_sequence_type_handler(typ, create_type_handler, **type_opts),
    collections.abc.MutableSequence: lambda typ, type_opts: create_mutable_sequence_type_handler(
        typ, create_type_handler, **type_opts
    ),
    tuple: lambda typ, type_opts: create_sequence_type_handler(typ, create_type_handler, **type_opts),
    collections.abc.Sequence: lambda typ, type_opts: create_sequence_type_handler(
        typ, create_type_handler, **type_opts
    ),
    # type_handlers/set.py
    # --------------------
    set: lambda typ, type_opts: create_mutable_set_type_handler(typ, create_type_handler, **type_opts),
    collections.abc.MutableSet: lambda typ, type_opts: create_mutable_set_type_handler(
        typ, create_type_handler, **type_opts
    ),
    # type_handlers/special.py
    # ------------------------
    Annotated: lambda typ, type_opts: create_annotated_type_handler(typ, create_type_handler, **type_opts),
    Union: lambda typ, type_opts: create_union_type_handler(typ, create_type_handler, **type_opts),
}


def register_type_handler_factory(typ: Any, factory: TypeHandlerFactory):
    def proxy(typ, type_opts):
        return factory(typ, **type_opts)

    _type_handler_map[typ] = proxy


def create_type_handler(typ: Any, /, **type_opts) -> TypeHandler:
    origin = get_origin(typ)
    handler = _type_handler_map.get(typ) if origin is None else _type_handler_map.get(origin)
    if handler is not None:
        return handler(typ, type_opts)
    if isinstance(typ, type):
        for base in typ.mro():
            handler = _type_handler_map.get(base)
            if handler is not None:
                return handler(typ, type_opts)
    raise UnsupportedTypeError(typ)
