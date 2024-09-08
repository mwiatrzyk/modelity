import dataclasses
import enum
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
    INVALID_ENUM = "modelity.InvalidEnum"


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


class ErrorFactory:
    """Factory class for making errors that can be reported by built-in types."""

    @staticmethod
    def create(loc: Loc, code: str, **data: Any) -> Error:
        """Generic error factory.

        :param loc:
            Error location.

        :param code:
            Error code.

        :param `**data`:
            Code-specific additional error data.

            Check specific factory methods for description of what parameters
            can be expected here.
        """
        return Error(loc, code, data)

    @classmethod
    def create_invalid_enum(cls, loc: Loc, tp: enum.Enum) -> Error:
        """Create invalid enum value error.

        Used by parser for :class:`enum.Enum` subclasses when it fails to map
        user input to supported list of enum values.

        Additional error data:

        ``supported_values``
            Tuple containing supported enum values.
        """
        return cls.create(loc, ErrorCode.INVALID_ENUM, supported_values=tuple(x for x in tp))
