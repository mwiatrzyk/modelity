from typing import Any, Optional, Tuple, Type

from modelity.interface import IError


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
    errors: Tuple[IError, ...]

    def __init__(self, errors: Tuple[IError, ...]):
        super().__init__()
        self.errors = errors


class ParsingError(ModelError):
    """Exception raised when model failed to parse input data."""

    def __str__(self):
        out = [f"parsing failed with {len(self.errors)} error(-s):"]
        for error in sorted(self.errors, key=lambda x: x.loc):
            out.append(f"  {error.loc}:")
            out.append(f"    {error.msg} [code={error.code}, data={error.data}]")
        return "\n".join(out)


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

    def __init__(self, model: Any, errors: Tuple[IError, ...]):
        super().__init__(errors)
        self.model = model

    def __str__(self):
        out = [f"validation of model {self.model.__class__.__qualname__!r} failed with {len(self.errors)} error(-s):"]
        for error in sorted(self.errors, key=lambda x: str(x.loc)):
            out.append(f"  {error.loc}:")
            out.append(f"    {error.msg} [code={error.code}, data={error.data}]")
        return "\n".join(out)


class UnsupportedType(ModelityError):
    """Raised when model is declared with field of unsupported type.

    Since Modelity uses lazy evaluation when it comes to type parser factory
    lookup, this error may be raised in the runtime, not during model class
    declaration.
    """

    __message_template__ = "unsupported type used: {self.tp!r}"

    #: The type that is not supported.
    tp: Type

    def __init__(self, tp: Type):
        super().__init__()
        self.tp = tp
