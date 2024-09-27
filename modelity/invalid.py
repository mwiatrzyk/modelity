import dataclasses
from typing import Any, Tuple

from .error import Error


class Invalid:
    """Special type representing invalid value.

    This allows to glue invalid input value with errors that it caused.
    """

    __slots__ = ("value", "errors")

    #: The given invalid value.
    value: Any

    #: The errors caused by value given by :attr:`value`
    errors: Tuple[Error, ...]

    @property
    def error_codes(self) -> Tuple[str, ...]:
        return tuple(x.code for x in self.errors)

    def __init__(self, value: Any, error: Error, *more_errors: Error):
        self.value = value
        self.errors = (error,) + more_errors

    def __repr__(self):
        return f"{self.__class__.__qualname__}(value={self.value!r}, error_codes={'+'.join(self.error_codes)})"
