import abc
from typing import Any, Iterator, Optional, Protocol, Tuple, Type, Union, TypeVar, Generic

from modelity.invalid import Invalid
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


class IParser(Protocol, Generic[T_co]):
    """Interface for type parsers."""

    @abc.abstractmethod
    def __call__(self, value: Any, loc: Loc) -> Union[T_co, Invalid]:
        """Try to parse given *value* of any type into instance of type *T*.

        On success, object of type *T* is returned. On failure, :class:`Invalid`
        object is returned.

        :param value:
            The value to be parsed.

        :param loc:
            The location of the value inside a model.
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

    def provide_type_parser(self, tp: Type[T], model_config: "IModelConfig") -> IParser[T]:
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

    def __call__(self, tp: Type[T], model_config: "IModelConfig") -> IParser[T]:
        """Create parser for given type.

        :param tp:
            The type to create parser for.

        :param model_config:
            Reference to the model configuration object.
        """


class IModelConfig(Protocol):
    """Protocol describing model configuration object."""

    #: Root type parser provider.
    #:
    #: This is used by model to find type parsers for its fields. This property
    #: can be overwritten by user to extend built-in parsing mechanism, or to
    #: completely replace with custom one that implements same interface.
    type_parser_provider: ITypeParserProvider

    #: Placeholder for user-defined data.
    #:
    #: This can be used to pass additional model-specific parameters to
    #: user-defined field pre- and postprocessors and/or validators.
    user_data: Optional[dict]


class IModel(abc.ABC):
    """Virtual base class for models.

    This is not used directly, but it is needed to register type parser for
    models.
    """
