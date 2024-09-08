import dataclasses
from typing import Any, Tuple, Type

from modelity.loc import Loc


class ErrorCode:
    NONE_REQUIRED = "modelity.NoneRequired"
    INTEGER_REQUIRED = "modelity.IntegerRequired"
    STRING_REQUIRED = "modelity.StringRequired"
    FLOAT_REQUIRED = "modelity.FloatRequired"
    BOOLEAN_REQUIRED = "modelity.BooleanRequired"
    ITERABLE_REQUIRED = "modelity.IterableRequired"
    MAPPING_REQUIRED = "modelity.MappingRequired"
    UNSUPPORTED_TYPE = "modelity.UnsupportedType"
    INVALID_TUPLE_FORMAT = "modelity.InvalidTupleFormat"


@dataclasses.dataclass
class Error:
    """Object describing error."""

    #: Location of the error.
    loc: Loc

    #: Error code.
    code: str

    #: Optional error data, with format depending on the :attr:`code`.
    data: dict = dataclasses.field(default_factory=dict)

    @classmethod
    def create(cls, loc: Loc, code: str, **data: Any) -> "Error":
        return cls(loc, code, data)

    @classmethod
    def create_unsupported_type(cls, loc: Loc, supported_types: Tuple[Type]) -> "Error":
        return cls.create(loc, ErrorCode.UNSUPPORTED_TYPE, supported_types=supported_types)

    @classmethod
    def create_invalid_tuple_format(cls, loc: Loc, expected_format: Tuple[Type]) -> "Error":
        return cls.create(loc, ErrorCode.INVALID_TUPLE_FORMAT, expected_format=expected_format)
