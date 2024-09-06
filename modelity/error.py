import dataclasses
from typing import Any, Tuple, Type


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
    loc: tuple

    #: Error code.
    code: str

    #: Optional error data, with format depending on the :attr:`code`.
    data: dict = dataclasses.field(default_factory=dict)

    @property
    def loc_str(self) -> str:
        """Location of the error formatted as string."""
        return ".".join(str(x) for x in self.loc)

    @classmethod
    def create(cls, loc: tuple, code: str, **data: Any) -> "Error":
        return cls(loc, code, data)

    @classmethod
    def create_unsupported_type(cls, loc: tuple, supported_types: Tuple[Type]) -> "Error":
        return cls.create(loc, ErrorCode.UNSUPPORTED_TYPE, supported_types=supported_types)

    @classmethod
    def create_invalid_tuple_format(cls, loc: tuple, expected_format: Tuple[Type]) -> "Error":
        return cls.create(loc, ErrorCode.INVALID_TUPLE_FORMAT, expected_format=expected_format)
