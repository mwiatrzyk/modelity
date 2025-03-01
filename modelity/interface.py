from numbers import Number
from typing import Any, Mapping, Protocol, Sequence, Set, Union, TypeVar, Generic

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


class IModelVisitor(Protocol):
    """Visitor interface for walking through the model data."""

    def visit_sequence_begin(self, loc: Loc, value: Sequence):
        """Begin visiting sequence value.

        :param loc:
            The location of the value.

        :param value:
            The visited value.
        """

    def visit_sequence_end(self, loc: Loc, value: Sequence):
        """End visiting sequence value.

        :param loc:
            The location of the value.

        :param value:
            The visited value.
        """

    def visit_mapping_begin(self, loc: Loc, value: Mapping):
        """Begin visiting mapping value.

        :param loc:
            The location of the value.

        :param value:
            The visited value.
        """

    def visit_mapping_end(self, loc: Loc, value: Mapping):
        """End visiting mapping value.

        :param loc:
            The location of the value.

        :param value:
            The visited value.
        """

    def visit_set_begin(self, loc: Loc, value: Set):
        """Begin visiting set value.

        :param loc:
            The location of the value.

        :param value:
            The visited value.
        """

    def visit_set_end(self, loc: Loc, value: Set):
        """End visiting set value.

        :param loc:
            The location of the value.

        :param value:
            The visited value.
        """

    def visit_model_begin(self, loc: Loc, value: IModel):
        """Begin visiting nested model object.

        :param loc:
            The location of the value.

        :param value:
            The visited value.
        """

    def visit_model_end(self, loc: Loc, value: IModel):
        """End visiting nested model object.

        :param loc:
            The location of the value.

        :param value:
            The visited value.
        """

    def visit_scalar(self, loc: Loc, value: Any):
        """Visit scalar value.

        Scalars are basically model fields that use simple types, like ints,
        strings, booleans etc.

        :param loc:
            The location of the value.

        :param value:
            The visited value.
        """

    def visit_none(self, loc: Loc, value: None):
        """Visit ``None`` value.

        :param loc:
            The location of the value.

        :param value:
            The visited value.
        """

    def visit_unset(self, loc: Loc, value: UnsetType):
        """Visit :class:`modelity.unset.UnsetType` value.

        This is called for model fields that have no value assigned.

        :param loc:
            The location of the value.

        :param value:
            The visited value.
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

    def accept(self, loc: Loc, value: T, visitor: IModelVisitor):
        """Apply model visitor.

        :param loc:
            The location of the *value* inside a model.

        :param value:
            The visited value.

        :param visitor:
            The visitor to apply.
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
