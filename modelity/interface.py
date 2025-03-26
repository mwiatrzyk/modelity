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

    def dump(self, loc: Loc, filter: "IDumpFilter") -> dict:
        """Serialize model to dict.

        :param loc:
            The location of this model if it is nested inside another model, or
            empty location otherwise.

        :param filter:
            The filter function.

            Check :class:`IDumpFilter` class for more details.
        """

    def validate(self, root: "IModel", ctx: Any, errors: list[Error], loc: Loc):
        """Validate this model.

        :param root:
            Reference to the root model.

            Root model is the model for which this method was initially called.
            This can be used by nested models to access entire model during
            validation.

        :param ctx:
            User-defined context object to be shared across all validators.

            It is completely transparent to Modelity, so any value can be used
            here, but recommended is ``None`` if no context is used.

        :param errors:
            List to populate with any errors found during validation.

            Should initially be empty.

        :param loc:
            The location of this model if it is nested inside another model, or
            empty location otherwise.
        """


class IModelValidatorCallable(Protocol):
    """Protocol describing model validator callable.

    Model validators are user-defined functions that run during validation
    phase and can operate at the model level, with access to all model
    fields.
    """

    def __call__(_, cls: type[IModel], self: IModel, root: IModel, ctx: Any, errors: list[Error], loc: Loc):
        """Run this model validator.

        :param cls:
            Validated model's type.

        :param self:
            Validated model's object.

        :param root:
            Root model object.

        :param ctx:
            User-defined context object.

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

    def validate(self, root: IModel, ctx: Any, errors: list[Error], loc: Loc, value: T):
        """Validate instance of this type inside a model.

        :param root:
            The reference to the root model.

            This is the model for which validation was initially started.

        :param ctx:
            The validation context object.

            This is user-defined object that is passed when validation is
            started and is shared across all validators during validation
            process. Can be used to pass some additional data that is needed by
            custom validators. For example, this can be used to validate a
            field against dynamically changing set of allowed values.

        :param errors:
            List of errors to populate with validation errors (if any).

        :param loc:
            The location of the *value* inside the model.

        :param value:
            The value to validate.

            It is guaranteed to be of type *T*.
        """
