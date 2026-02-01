from io import StringIO
from typing import Any, Optional

from modelity import _utils
from modelity.error import Error, ErrorWriter

__all__ = export = _utils.ExportList()  # type: ignore


@export
class ModelityError(Exception):
    """Base class for every Modelity-specific exception."""

    #: Message template string.
    #:
    #: Used as default error message when specified. Properties of the current
    #: exception object can be provided via ``self`` placeholder.
    __message_template__: Optional[str] = None

    def __str__(self) -> str:
        if self.__message_template__ is None:
            return super().__str__()
        return self.__message_template__.format(self=self)


@export
class UnsupportedTypeError(ModelityError):
    """Raised when model is declared with a field of a type that is not
    supported by the current version of Modelity library."""

    __message_template__ = "unsupported type used: {self.typ!r}"

    #: The type that is not supported.
    typ: type

    def __init__(self, typ: type):
        super().__init__()
        self.typ = typ


@export
class ModelError(ModelityError):
    """Common base class for errors raised during either data parsing or model
    validation stages.

    It can be used by library clients to catch both parsing and validation
    errors in one place, which can help avoid unexpected leaking of exceptions
    the user was not aware of.

    :param typ:
        The type for which this error has happened.

    :param errors:
        Tuple of errors to initialize exception with.
    """

    #: The type for which this error has happened.
    #:
    #: .. versionchanghttps://stackoverflow.com/questions/49220022/how-can-mypy-ignore-a-single-line-in-a-source-fileed:: 0.28.0
    #:      Moved from :class:`ParsingError` class and now made available for all
    #:      subclasses for ease of use.
    typ: type

    #: Tuple with either parsing, or validation errors.
    errors: tuple[Error, ...]

    def __init__(self, typ: type, errors: tuple[Error, ...]):
        super().__init__()
        self.typ = typ
        self.errors = errors

    @property
    def typ_name(self) -> str:
        """Return the name of the type."""
        return _utils.describe(self.typ)


@export
class ParsingError(ModelError):
    """Exception raised at parsing stage when input data could not be parsed
    into model instance.

    When this exception is raised, no model is created.
    """

    def __str__(self) -> str:
        error_count = len(self.errors)
        error_or_errors = "error" if error_count == 1 else "errors"
        buffer = StringIO()
        writer = ErrorWriter(buffer, indent_level=1, show_code=True, show_value_type=True, show_data=True)
        for error in sorted(self.errors, key=lambda x: x.loc):
            writer.write(error)
        return f"Found {error_count} parsing {error_or_errors} for type {self.typ_name!r}:\n{buffer.getvalue().rstrip()}"


@export
class ValidationError(ModelError):
    """Exception raised at model validation stage when one or model specific
    constraint are broken.

    This exception may only be raised for existing models.

    :param model:
        The model for which validation has failed.

        This will be the root model, i.e. the one for which
        :meth:`modelity.model.Model.validate` method was called.

    :param errors:
        Tuple containing all validation errors.
    """

    #: The model object for which validation has failed.
    model: Any

    def __init__(self, model: Any, errors: tuple[Error, ...]):
        super().__init__(model.__class__, errors)
        self.model = model

    def __str__(self) -> str:
        error_count = len(self.errors)
        error_or_errors = "error" if error_count == 1 else "errors"
        buffer = StringIO()
        writer = ErrorWriter(buffer, indent_level=1, show_code=True, show_data=True)
        for error in sorted(self.errors, key=lambda x: x.loc):
            writer.write(error)
        return f"Found {error_count} validation {error_or_errors} for model {self.typ_name!r}:\n{buffer.getvalue().rstrip()}"
