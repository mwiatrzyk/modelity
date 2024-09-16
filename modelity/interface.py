import abc
from typing import Any, Protocol, Tuple, Type

from modelity.error import Error
from modelity.loc import Loc


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
    def validate(self, root_model: "IModel" = None):
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


class IModelValidator(Protocol):
    """Interface for model validators.

    Returned by :meth:`modelity.model.model_validator` decorator.
    """

    def __call__(
        self, cls: Type[IModel], model: IModel, errors: Tuple[Error, ...], root_model: IModel = None
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
