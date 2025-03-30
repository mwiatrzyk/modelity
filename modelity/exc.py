from typing import Any, Optional

from modelity.error import Error


class ModelityError(Exception):
    """Base class for Modelity-specific exceptions."""

    __message_template__: Optional[str] = None

    def __str__(self) -> str:
        if self.__message_template__ is None:
            return super().__str__()
        return self.__message_template__.format(self=self)


class ModelError(ModelityError):
    """Common base class for errors that model may raise during either parsing,
    or validation phases.

    It can be used in client code to catch both parsing and validation errors
    by using this single exception type, which can help avoid unexpected
    leaking of exceptions the user was not aware of. However, it is still
    possible to use subclasses of this exception explicitly.

    :param errors:
        Tuple of errors to initialize exception with.
    """

    #: Tuple with either parsing, or validation errors.
    errors: tuple[Error, ...]

    def __init__(self, errors: tuple[Error, ...]):
        super().__init__()
        self.errors = errors


class ParsingError(ModelError):
    """Exception raised when type parser fails to parse input value into
    instance of desired type."""

    #: The type for which parsing has failed.
    typ: Any

    def __init__(self, typ: Any, errors: tuple[Error, ...]):
        super().__init__(errors)
        self.typ = typ

    @property
    def typ_name(self) -> str:
        """Return the name of the type."""
        name = getattr(self.typ, "__qualname__", None)
        if name is not None:
            return name
        return repr(self.typ)

    @property
    def formatted_errors(self) -> str:
        """The string containing formatted :attr:`errors` attribute."""
        out = []
        for error in sorted(self.errors, key=lambda x: x.loc):
            out.append(f"  {error.loc}:")
            out.append(f"    {error.msg} [code={error.code}, value_type={error.value_type!r}]")
        return "\n".join(out)

    def __str__(self):
        return f"parsing failed for type {self.typ_name!r} with {len(self.errors)} error(-s):\n{self.formatted_errors}"


class ValidationError(ModelError):
    """Exception raised when model validation failed.

    :param model:
        The model for which validation has failed.

        This will be the root model, i.e. the one for which
        :meth:`modelity.model.Model.validate` method was called.

    :param errors:
        Tuple containing all validation errors.
    """

    #: The model for which validation has failed.
    model: Any

    def __init__(self, model: Any, errors: tuple[Error, ...]):
        super().__init__(errors)
        self.model = model

    def __str__(self):
        out = [f"validation of model {self.model.__class__.__qualname__!r} failed with {len(self.errors)} error(-s):"]
        for error in sorted(self.errors, key=lambda x: str(x.loc)):
            out.append(f"  {error.loc}:")
            out.append(f"    {error.msg} [code={error.code}, data={error.data}]")
        return "\n".join(out)


class UnsupportedTypeError(ModelityError):
    """Raised when model is declared with a field of a type that is not
    supported by the current version of Modelity library."""

    __message_template__ = "unsupported type used: {self.typ!r}"

    #: The type that is not supported.
    typ: type

    def __init__(self, typ: type):
        super().__init__()
        self.typ = typ
