import dataclasses
from typing import Any, Tuple, Type


class ErrorCode:
    NONE_REQUIRED = "modelity.NoneRequired"
    INTEGER_REQUIRED = "modelity.IntegerRequired"
    STRING_REQUIRED = "modelity.StringRequired"
    UNSUPPORTED_TYPE = "modelity.UnsupportedType"
    FLOAT_REQUIRED = "modelity.FloatRequired"
    BOOLEAN_REQUIRED = "modelity.BooleanRequired"


@dataclasses.dataclass
class Error:
    """Object describing error."""

    #: Location of the error.
    loc: tuple

    #: Error code.
    code: str

    #: Optional error data, with format depending on the :attr:`code`.
    data: dict = dataclasses.field(default_factory=dict)

    @classmethod
    def create(cls, loc: tuple, code: str, **data: Any) -> "Error":
        return cls(loc, code, data)

    @classmethod
    def create_unsupported_type(cls, loc: tuple, supported_types: Tuple[Type]) -> "Error":
        return cls.create(loc, ErrorCode.UNSUPPORTED_TYPE, supported_types=supported_types)
