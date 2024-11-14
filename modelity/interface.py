import abc
from typing import Any, Iterator, Optional, Protocol, Tuple, Type, Union, TypeVar, Generic

from modelity.loc import Loc

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")


class ISupportsLessEqual(Protocol):
    """Interface for objects that contain less and less or equal operator."""

    def __lt__(self, other: object) -> bool: ...

    def __le__(self, other: object) -> bool: ...


class IDumpFilter(Protocol):
    """Interface for functions to be used with :meth:`IModel.dump` method."""

    def __call__(self, value: Any, loc: Loc) -> Tuple[Any, bool]:
        """Prepare value to be placed in the resulting dictionary.

        This method must return 2-element tuple, where:

        * 1st element is the output value (which may be different than *value*),
        * 2nd element is the boolean value stating that the currently processed
          value should be skipped (if set to ``True``), or accepted (if set to
          ``False``).

        These functions can be used both for converting model's values before
        putting to the dict (f.e. when JSON-capable dict is required), or just
        to remove certain values (f.e. unset ones) from the resulting dict.

        :param value:
            The value to be processed.

        :param loc:
            The location of the value inside model tree.
        """


class IError(Protocol):
    """Protocol specifying error object."""

    #: Location of the error.
    loc: Loc

    #: Error code.
    code: str

    #: Error data.
    #:
    #: This contains code-specific data and can be used to render parametric
    #: error messages.
    data: Optional[dict] = None

    #: Formatted error message.
    #:
    #: This is what will be printed by default when error happens. Custom error
    #: creators can be used to render messages for custom error, or to change
    #: messages for built-in errors.
    msg: Optional[str] = None


class IInvalid(Protocol):
    """Protocol specifying invalid value."""

    #: The value that is invalid.
    value: Any

    #: Tuple of errors found for the value.
    errors: Tuple[IError, ...]


class IParser(Protocol, Generic[T_co]):
    """Interface for type parsers."""

    @abc.abstractmethod
    def __call__(self, value: Any, loc: Loc, config: "IConfig") -> Union[T_co, IInvalid]:
        """Try to parse given *value* of any type into instance of type *T*.

        On success, object of type *T* is returned. On failure, :class:`Invalid`
        object is returned.

        :param value:
            The value to be parsed.

        :param loc:
            The location of the value inside a model.

        :param config:
            Model config object.
        """


class ITypeParserProvider(Protocol):
    """Interface for collections of type parsers."""

    def iter_types(self) -> Iterator[Type]:
        """Return iterator yielding types registered for this provider."""

    def has_type(self, tp: Type) -> bool:
        """Check if this provider has parser factory declared for given type.

        :param tp:
            The type to be checked.
        """

    def get_type_parser_factory(self, tp: Type[T]) -> Optional["ITypeParserFactory[T]"]:
        """Get type parser factory for given type or ``None`` if no factory was
        registered for type *tp*.

        :param tp:
            The type to retrieve parser factory for.
        """

    def provide_type_parser(self, tp: Type[T], model_config: "IConfig") -> IParser[T]:
        """Provide parser for given type.

        Returns parser for given type *tp* or raises
        :exc:`modelity.exc.UnsupportedType` if parser was not found.

        :param tp:
            The type to find parser for.

        :param model_config:
            Model configuration object.

            This allows to access both built-in and user-defined model settings
            from type parser factories.
        """


class ITypeParserFactory(Protocol, Generic[T]):
    """Interface for type parser factory functions."""

    def __call__(self, tp: Type[T], model_config: "IConfig") -> IParser[T]:
        """Create parser for given type.

        :param tp:
            The type to create parser for.

        :param model_config:
            Reference to the model configuration object.
        """


class IErrorCreator(Protocol):
    """Protocol specifying error factory function."""

    def __call__(self, loc: Loc, code: str, data: Optional[dict]=None) -> IError:
        """Create error object.

        :param loc:
            Location of the error.

        :param code:
            Error code.

        :param data:
            Error data.

            The structure of this argument depends on the error code.
        """


class IConfig(Protocol):
    """Protocol describing model configuration object."""

    #: Root type parser provider.
    #:
    #: This is used by model to find type parsers for its fields. This property
    #: can be overwritten by user to extend built-in parsing mechanism, or to
    #: completely replace with custom one that implements same interface.
    type_parser_provider: ITypeParserProvider

    #: Function used to create both parsing and validation errors.
    #:
    #: By default, built-in error creator is used, but this can be replaced
    #: with custom one that may still use built-in error creator if needed.
    create_error: IErrorCreator

    #: Placeholder for user data.
    #:
    #: This can be used use this to pass user-defined additional data to custom
    #: parsers and/or validators.
    user_data: Optional[dict]


class IModel(abc.ABC):
    """Virtual base class for models.

    This is not used directly, but it is needed to register type parser for
    models.
    """

    @abc.abstractmethod
    def set_config(self, config: IConfig):
        """Set config to be used by this model.

        This overrides static config provided by :attr:`IModel.__config__`
        attribute and can be used if it is needed change default config object
        just for particular instance, not for all instances.

        :param config:
            New config object.
        """

    @abc.abstractmethod
    def set_loc(self, loc: Loc):
        """Set root location for this model.

        Root location will be used to prefix locations of all errors that may
        be reported by this model. By default, each model has root location set
        to empty location. By using this method it is possible to prefix all
        errors with user defined prefix whenever needed (f.e. when this model
        is used as a field in a dataclass).

        :param loc:
            New root location.
        """
