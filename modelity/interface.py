import abc
from typing import Any, Iterator, Mapping, Optional, Protocol, Tuple, Type, Union, TypeVar, Generic

from modelity.error import Error
from modelity.field import BoundField
from modelity.invalid import Invalid
from modelity.loc import Loc

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")


class ISupportsLess(Protocol):
    """Interface for objects that contain less operator."""

    def __lt__(self, other: object) -> bool: ...


class IDumpFilter(Protocol):
    """Interface for :meth:`IModel.dump` method filter callable."""

    def __call__(self, loc: Loc, value: Any) -> Tuple[Any, bool]: ...


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

    def provide_type_parser(self, tp: Type[T], root: Optional["ITypeParserProvider"] = None) -> IParser[T]:
        """Provide parser for given type.

        Returns parser for given type or raises
        :exc:`modelity.exc.UnsupportedType` if parser was not found.

        :param tp:
            The type to find parser for.

        :param root:
            The root parser provider.

            This will be passed to type parser factories and can be used to
            access root provider to find parser for nested types. Normally it
            is not required to pass this argument, as it defaults to *self*.
            However, it might be necessary to override this when calling
            :meth:`provide_type_parser` from behind a proxy class.
        """


class ITypeParserFactory(Protocol, Generic[T]):
    """Interface for type parser factory functions."""

    def __call__(self, provider: ITypeParserProvider, tp: Type[T]) -> IParser[T]:
        """Create parser for given type.

        :param provider:
            Reference to the root provider.

        :param tp:
            The type to create parser for.
        """


class IModelConfig(Protocol):
    """Interface for model configuration data."""

    #: Type parser provider to use.
    #:
    #: Type parser provider is used to find parser for field type.
    type_parser_provider: ITypeParserProvider

    #: Placeholder for user-defined data.
    user_data: dict


class IModelMeta(abc.ABCMeta):
    """Base class for model metaclass.

    This is here only to be used to annotate model class properties for the
    purpose of being used in type annotations across the library.
    """

    #: Model configuration.
    #:
    #: This can be used to override or extend built-in defaults.
    __config__: IModelConfig

    #: Read-only property allowing to access model's fields.
    __fields__: Mapping[str, BoundField]


class IModel(metaclass=IModelMeta):
    """Interface for models."""

    @abc.abstractmethod
    def set_loc(self, loc: Loc):
        """Set location of this model.

        This affects the location prefix of potential parsing and/or validation
        errors reported for this model.
        """

    @abc.abstractmethod
    def get_loc(self) -> Loc:
        """Get location of this model.

        If :meth:`set_loc` was not used before, then this returns empty location
        object.
        """

    @abc.abstractmethod
    def validate(self, root_model: Optional["IModel"] = None):
        """Validate this model.

        In modelity, validation is separated from parsing. While parsing is
        performed automatically when model instances are created or modified,
        validation must be invoked explicitly by calling this method.

        This method will raise :exc:`modelity.exc.ValidationError` if model is
        invalid, or return without raising exceptions otherwise.

        :param root_model:
            The root model.

            This argument is only used when this model appears as a field in
            another, parent model. It must point to the root model, which is the
            one for which :meth:`validate` was called.
        """

    @abc.abstractmethod
    def dump(self, func: Optional[IDumpFilter] = None) -> dict:
        """Convert this model to dict.

        This method will recursively dump nested models, mappings and sequences.

        :param func:
            Optional filter function.

            Can be used to exclude fields from the resulting dict, remove
            certain values and convert to different value whenever needed.

            See :class:`IDumpFilter` protocol to check how to use this.
        """
