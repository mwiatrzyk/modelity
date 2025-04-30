from typing import Any, Protocol, Union, TypeVar, Generic

from modelity.error import Error
from modelity.loc import Loc
from modelity.unset import UnsetType

T = TypeVar("T")


#: A sentinel value indicating that the return value or the input arguments
#: should be discarded by the caller.
#:
#: Currently used only by the :meth:`IDumpFilter.__call__` method.
DISCARD = object()


class IModel(Protocol):
    """Protocol describing common interface for data models."""

    #: The root location of the model.
    #:
    #: If the model is a root model, then root location is empty. Otherwise, if
    #: the model is nested inside another model, root location points to a field
    #: in parent model when nested model object is attached to.
    #:
    #: This property is automatically assigned by Modelity internals and should
    #: not be modified by hand.
    __loc__: Loc

    def dump(self, filter: "IDumpFilter") -> dict:
        """Serialize model to a JSON-compatible dict.

        :param filter:
            The filter function.

            It can be used to discard values from the output or to modify the
            value before it gets written to the output. The most trivial
            implementation that does nothing is:

            .. testcode::

                def dump_filter(loc, value):
                    return value

            Check :class:`IDumpFilter` class for more details.
        """

    def validate(self, root: "IModel", ctx: Any, errors: list[Error]):
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
        """


class IModelValidationHook(Protocol):
    """Protocol describing interface of the model-level validation hooks.

    Model validators are user-defined functions that run during validation
    phase and can operate at the model level, with access to all model
    fields no matter if those fields are set or not.
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


class IFieldValidationHook(Protocol):
    """Protocol describing interface of the field-level validation hooks.

    Field validators are executed for selected fields and only if those fields
    have values set.
    """

    def __call__(_, cls: type[IModel], self: IModel, root: IModel, ctx: Any, errors: list[Error], loc: Loc, value: Any):
        """Perform field validation.

        :param cls:
            Model type.

        :param self:
            The model that owns validated field.

        :param root:
            The root model.

        :param ctx:
            User-defined context object.

        :param errors:
            List of errors to be modified when errors are found.

        :param loc:
            Field's location in the model.

        :param value:
            Field's value.
        """


class IFieldParsingHook(Protocol):
    """Protocol describing interface of the user-defined field parsing hooks.

    When field is initialized with a value, then just type parsing is normally
    performed by the Modelity library and based on the results of the parsing
    itself, Modelity can determine if the value was positively parsed or not.
    However, built-in parsing is very restrictive and will not perform any
    cleanup on the input value by its own. Instead, Modelity allows to create
    two kind of user-defined parsing hooks:

    * **preprocessors**, running **before** the value is parsed,
    * **postprocessors**, running **after** the parsing and **only** if the
      parsing **has succeeded**.

    Preprocessors can be used to perform value filtering (like white character
    stripping), while postprocessors can be used to perform field-specific
    additional checks each time the value is changed.

    Both hooks share common interface defined by this protocol.
    """

    def __call__(_, cls: type[IModel], errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
        """Call field processing hook.

        :param cls:
            Model's type.

        :param errors:
            List of errors.

            Can be modified by the hook if the hook fails.

        :param loc:
            The location of the currently processed field.

        :param value:
            The processed value.
        """


class IDumpFilter(Protocol):
    """Protocol describing interface of the filter function used by
    :meth:`modelity.model.Model.dump` method."""

    def __call__(self, loc: Loc, value: Any) -> Any:
        """Apply the filter to a model's field.

        This method is invoked for each field in the model, regardless of whether
        the field is set or unset. It should return the serialized value for a
        field, or :obj:`DISCARD` to discard the field from the serialized
        output.

        :param loc:
            The location of the current value in the model.

        :param value:
            The current value.

        :return:
            The value to use for a field or :obj:`DISCARD` to discard currently
            processed value from the serialized output.
        """


class IConstraint(Protocol):
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
