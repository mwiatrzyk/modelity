import copy
import dataclasses
import functools
from typing import (
    Any,
    Callable,
    ClassVar,
    Iterator,
    Mapping,
    Optional,
    Union,
    TypeVar,
    cast,
    get_args,
    get_origin,
)
import typing_extensions

from modelity._internal import hooks as _int_hooks, model as _int_model
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.interface import (
    IField,
    IModelVisitor,
    ITypeDescriptor,
)
from modelity.loc import Loc
from modelity.types import is_deferred, is_any_optional, is_unsettable
from modelity.unset import Unset, UnsetType
from modelity import _utils

from .base import field_info, FieldInfo, Field, Model, ModelMeta

__all__ = ["Model", "FieldInfo", "field_info"]
