from typing import Any, Tuple

from .error import Error


class Invalid:
    """Special type representing invalid value.

    This allows to glue invalid input value with errors that it caused.
    """

    #: The given invalid value.
    value: Any

    #: The errors caused by value given by :attr:`value`
    errors: Tuple[Error]

    def __init__(self, value: Any, error: Error, *more_errors: Error):
        self.value = value
        self.errors = (error,) + more_errors

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__qualname__}(value={self.value!r})>"
