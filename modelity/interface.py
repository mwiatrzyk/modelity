from typing import Any, Protocol, Union, TypeVar, Generic

from modelity.error import Error
from modelity.loc import Loc
from modelity.unset import UnsetType

T = TypeVar("T")


class IModel(Protocol):
    """Protocol describing model interface.

    The only purpose of this interface is to provide type hints for functions
    that use models. To check if the object is a model, please use
    :func:`isinstance` function with :class:`modelity.model.Model` class.
    """


class IModelValidatorCallable(Protocol):
    """Protocol describing model validator callable.

    Model validators are user-defined functions that run during validation
    phase and can operate at the model level, with access to all model
    fields.
    """

    def __call__(_, cls: type[IModel], self: IModel, root: IModel, errors: list[Error], loc: Loc):
        """Run this model validator.

        :param cls:
            Validated model's type.

        :param self:
            Validated model's object.

        :param root:
            Root model object.

        :param errors:
            List of errors to be modified with errors found.

        :param loc:
            The location of the *self* model.

            Will be empty for root model, and non-empty if the model is nested
            inside some other model.
        """


class IDumpFilter(Protocol):
    """Protocol describing model field filtering function used during model
    serialization."""

    #: Special return value for field exclusion from the output.
    SKIP = object()

    def __call__(self, loc: Loc, value: Any) -> Any:
        """Apply the filter to a model's field.

        This method is invoked for each field in the model, regardless of whether
        the field is set or unset. It determines the value to be included in the
        serialized output.

        To exclude a field from the output, return :obj:`IDumpFilter.SKIP`.

        :param loc:
            The location of the current field.

        :param value:
            The current value of the field.

        :return:
            The processed value or :obj:`IDumpFilter.SKIP` to exclude it.
        """


class IConstraintCallable(Protocol):
    """Protocol describing constraint callable.

    Constraint callables can be used with :class:`typing.Annotated`-wrapped
    types.
    """

    def __call__(self, errors: list[Error], loc: Loc, value: Any) -> bool:
        """Invoke constraint checking on given value and location.

        On success, when value satisfies the constraint, ``True`` is returned.

        On failure, when value does not satisfy the constraint, ``False`` is
        returned and *errors* list is populated with constraint-specific
        error(-s).

        :param errors:
            List of errors to be updated with errors found.

        :param loc:
            The location of the value.

            Used to create error instance if constraint fails.

        :param value:
            The value to be verified with this constraint.
        """


class ITypeDescriptor(Protocol, Generic[T]):
    """Protocol describing type.

    This interface is used by Modelity internals to parse type, dump it and
    validate.
    """

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Union[T, UnsetType]:
        """Parse instance of type *T* from provided *value*.

        If parsing is successful, then instance of type *T* is returned, with
        value parsed from *value*.

        If parsing failed, then ``Unset`` is returned and *errors* list is
        populated with one or more error objects.

        :param errors:
            List of errors.

            Can be modified by parser implementation.

        :param loc:
            The location of the *value* inside the model.

        :param value:
            The value to parse.
        """

    def dump(self, loc: Loc, value: T, filter: IDumpFilter) -> Any:
        """Serialize value to a nearest JSON type.

        This method should return any of the following:

        * dict
        * list
        * number
        * string
        * boolean
        * ``None``
        * :obj:`IDumpFilter.SKIP`.

        :param loc:
            The location of current value inside a model.

        :param value:
            The current value.

        :param filter:
            The value filtering function.

            Check :class:`IDumpFilter` for more details.
        """

    def validate(self, errors: list[Error], loc: Loc, value: T):
        """Validate instance of this type inside a model.

        :param errors:
            List of errors to populate with validation errors (if any).

        :param loc:
            The location of the *value* inside the model.

        :param value:
            The value to validate.

            It is guaranteed to be of type *T*.
        """
