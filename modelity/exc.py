from typing import Tuple, Type

from modelity.error import Error


class ModelityError(Exception):
    """Base class for Modelity-specific exceptions."""

    __message_template__: str = None

    def __str__(self) -> str:
        if self.__message_template__ is None:
            return super().__str__()
        return self.__message_template__.format(self=self)


class ParsingError(ModelityError):
    """Raised when it was not possible to parse input value to an expected type."""

    #: Tuple with parsing errors
    errors: Tuple[Error, ...]

    def __init__(self, errors: Tuple[Error, ...]):
        super().__init__()
        self.errors = errors

    def __str__(self):
        out = [f"parsing failed with {len(self.errors)} error(-s):"]
        for error in sorted(self.errors, key=lambda x: x.loc):
            out.append(f"  {error.loc}:")
            out.append(f"    {error.code} {error.data}")
        return "\n".join(out)


class UnsupportedType(ModelityError):
    """Raised when type is unsupported.

    This can be solved by manually registering type if this is not a bug, but a
    custom type not known to Modelity was used.
    """

    __message_template__ = "unsupported type used: {self.tp!r}"

    #: The type that is not supported.
    tp: Type

    def __init__(self, tp: Type):
        super().__init__()
        self.tp = tp
