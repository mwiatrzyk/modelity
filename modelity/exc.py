from typing import Any, Callable, Literal, Optional, cast

from modelity import _utils
from modelity.error import Error

__all__ = export = _utils.ExportList()  # type: ignore


def _sort_by_loc(error: Error) -> Any:
    return error.loc


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

    def format_errors(
        self,
        indent_string: str = "  ",
        indent_level: int = 0,
        sort_key: Optional[Callable[[Error], Any]] = None,
        show_code: bool = False,
        show_value: bool = False,
        show_value_type: bool = False,
        show_data: bool = False,
    ) -> str:
        """Format error list as string.

        Returns errors formatted according to options provided.

        .. versionadded:: 0.28.0
            This method replaced ``formatted_errors`` property used earlier.

        :param indent_string:
            Indentation string.

        :param indent_level:
            Indentation level.

        :param sort_key:
            Sort errors using given sort key or set to ``None`` to disable
            sorting.

        :param show_code:
            Display error code for each formatted error.

        :param show_value:
            Display value for each formatted error.

        :param show_value_type:
            Display value type for each formatted error.

        :param show_data:
            Display content of :attr:`modelity.error.Error.data` attribute.
        """
        out = []
        loc_indent = indent_string * indent_level
        msg_indent = indent_string * (indent_level + 1)
        if sort_key is not None:
            errors = sorted(self.errors, key=sort_key)
        else:
            errors = cast(list[Error], self.errors)
        for error in errors:
            params = {}
            if show_code:
                params["code"] = error.code
            if show_value:
                params["value"] = str(error.value)
            if show_value_type:
                params["value_type"] = error.value.__class__.__name__
            if show_data:
                params.update((k, self._format_any(v)) for k, v in error.data.items())
            params_str = ", ".join(f"{k}={v}" for k, v in params.items())
            if params_str:
                params_str = f" [{params_str}]"
            out.append(f"{loc_indent}{error.loc}:")
            out.append(f"{msg_indent}{error.msg}{params_str}")
        return "\n".join(out)

    @classmethod
    def _format_any(cls, obj: Any) -> str:
        if isinstance(obj, list):
            return cls._format_list(obj)
        if isinstance(obj, type):
            return obj.__name__
        if isinstance(obj, str):
            return repr(obj)
        return str(obj)

    @classmethod
    def _format_list(cls, obj: list) -> str:
        return f"[{', '.join(cls._format_any(x) for x in obj)}]"


@export
class ParsingError(ModelError):
    """Exception raised at parsing stage when input data could not be parsed
    into model instance.

    When this exception is raised, no model is created.
    """

    def __str__(self) -> str:
        error_count = len(self.errors)
        error_or_errors = "error" if error_count == 1 else "errors"
        formatted_errors = self.format_errors(
            indent_level=1, sort_key=_sort_by_loc, show_code=True, show_value_type=True, show_data=True
        )
        return f"Found {error_count} parsing {error_or_errors} for type {self.typ_name!r}:\n{formatted_errors}"


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
        formatted_errors = self.format_errors(indent_level=1, sort_key=_sort_by_loc, show_code=True, show_data=True)
        return f"Found {error_count} validation {error_or_errors} for model {self.typ_name!r}:\n{formatted_errors}"
