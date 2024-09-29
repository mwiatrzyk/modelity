import abc
from typing import Any, Optional, Protocol, Tuple, Type, Union, TypeVar, Generic

from modelity.error import Error
from modelity.invalid import Invalid
from modelity.loc import Loc

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")


class ISupportsLess(Protocol):

    def __lt__(self, other: object) -> bool: ...


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

    def provide_type_parser(self, tp: Type[T], root: Optional["ITypeParserProvider"]=None) -> IParser[T]:
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


class IModel(abc.ABC):
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


class IFieldProcessor(Protocol):
    """Interface for model fields' pre- and postprocessors."""

    def __call__(self, cls: Type[IModel], loc: Loc, name: str, value: Any) -> Union[Any, Invalid]:
        """Execute value processor.

        If processor fails to process ``value``, then :class:`Invalid` object
        should be returned. Otherwise it should return output value that will be
        used as input to the next processor.

        :param cls:
            Model type.

        :param loc:
            The location of the processed field inside a model.

            It already includes field's name.

        :param name:
            Field's name.

        :param value:
            Field's value.
        """


class IModelValidator(Protocol):
    """Interface for model validators.

    Returned by :meth:`modelity.model.model_validator` decorator.
    """

    def __call__(
        self, cls: Type[IModel], model: IModel, errors: Tuple[Error, ...], root_model: Optional[IModel] = None
    ) -> Tuple[Error, ...]:
        """Execute model validator.

        :param cls:
            Model class.

        :param model:
            Model instance.

            This is the instance validated by this validator.

        :param errors:
            Tuple with validation errors collected so far.

        :param root_model:
            Reference pointing to root model, which is the one for which
            :meth:`modelity.model.Model.validate` was called.

            Can be used to access whole model if ``model`` is nested in another
            model.
        """


class IFieldValidator(Protocol):
    """Interface for field validators.

    Returned by :meth:`modelity.model.field_validator` decorator.
    """

    def __call__(self, cls: Type[IModel], model: IModel, name: str, value: Any) -> Tuple[Error, ...]:
        """Execute field validator.

        :param cls:
            Model class.

        :param model:
            Model instance.

            This is the instance validated by this validator.

        :param name:
            Name of a field that is currently being validated by this validator.

        :param value:
            Value of a field that is currently being validated by this validator.
        """
