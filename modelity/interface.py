import abc
from numbers import Number
from typing import Any, Mapping, Optional, Protocol, Sequence, Set, Union, TypeVar, Generic

from modelity import _utils
from modelity.error import Error
from modelity.loc import Loc
from modelity.unset import UnsetType

__all__ = export = _utils.ExportList()  # type: ignore

T = TypeVar("T")


@export
class IBaseHook(Protocol):
    """Base class for hook protocols.

    Hooks are used to wrap user-defined functions and use them to inject extra
    logic to either parsing or validation stages of model's data processing.
    """

    #: The sequential ID number assigned for this hook.
    #:
    #: This is used to sort hooks by their declaration order when they are
    #: collected from the model.
    __modelity_hook_id__: int

    #: The name of this hook.
    __modelity_hook_name__: str

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        """Invoke this hook."""
        ...


@export
class IModelHook(IBaseHook):
    """Protocol describing model-level hooks.

    This kind of hooks are executed on model instances.
    """


@export
class IFieldHook(IBaseHook):
    """Protocol describing field-level hooks.

    This kind of hooks are executed on model fields independently.
    """

    #: Field names this hook will be used for.
    #:
    #: Empty set means that it will be used for all fields, non-empty set means
    #: that it will be used for a subset of model fields.
    __modelity_hook_field_names__: set[str]


@export
class IConstraint(abc.ABC):
    """Abstract base class for constraints.

    Constraints can be used with :class:`typing.Annotated`-wrapped types to
    restrict value range or perform similar type-specific validation when field
    is either set or modified.

    In addition, constraints are also verified again during validation stage.
    """

    @abc.abstractmethod
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


@export
class ISupportsValidate(abc.ABC, Generic[T]):
    """Interface to be implemented by type descriptors that need to provide
    some extra type-specific validation logic.

    As an example, let's think of type constraint handling. Constraints can be
    checked and verified during model construction, but since the model is
    mutable and can be modified later the constraints may need double checking
    at validation stage.

    .. versionadded:: 0.17.0
    """

    @abc.abstractmethod
    def validate(self, errors: list[Error], loc: Loc, value: T):
        """Validate value of type *T*.

        :param errors:
            Mutable list of errors.

        :param loc:
            The location of the *value* inside the model.

        :param value:
            The value to validate.

            It is guaranteed to be an instance of type *T*.
        """


@export
class ITypeDescriptor(abc.ABC, Generic[T]):
    """Protocol describing type.

    This interface is used by Modelity internals to enclose type-specific
    parsing, validation and visitor accepting logic. Whenever a new type is
    added to a Modelity library it will need a dedicated implementation of this
    interface.
    """

    @abc.abstractmethod
    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Union[T, UnsetType]:
        """Parse object of type *T* from a given *value* of any type.

        If parsing is successful, then instance of type *T* is returned, with
        value parsed from *value*. If *value* already is an instance of type
        *T* then unchanged *value* can be returned (but does not have to).

        If parsing failed, then ``Unset`` is returned and *errors* list is
        populated with one or more error objects explaining why the *value*
        could not be parsed as *T*.

        :param errors:
            List of errors.

        :param loc:
            The location of the *value* inside the model.

        :param value:
            The value to parse.
        """

    @abc.abstractmethod
    def accept(self, visitor: "IModelVisitor", loc: Loc, value: T):
        """Accept given model visitor.

        :param visitor:
            The visitor to accept.

        :param loc:
            The location of the value inside model.

        :param value:
            The value to process.

            It is guaranteed to be an instance of type *T*.
        """


@export
class ITypeDescriptorFactory(Protocol, Generic[T]):
    """Protocol describing type descriptor factories.

    These functions are used to create instances of :class:`ITypeDescriptor`
    for provided type and type options.

    .. versionchanged:: 0.17.0
        This protocol was made generic.
    """

    def __call__(self, typ: Any, type_opts: dict) -> ITypeDescriptor[T]:
        """Create type descriptor for a given type.

        :param typ:
            The type to create descriptor for.

            Can be either simple type, or a special form created using helpers
            from the :mod:`typing` module.

        :param type_opts:
            Type-specific options injected directly from a model when
            :class:`modelity.model.Model` subclass is created.

            Used to customize parsing, dumping and/or validation logic for a
            provided type.

            If not used, then it should be set to an empty dict.
        """
        ...


@export
class IModelVisitor(abc.ABC):
    """Base class for model visitors.

    The visitor mechanism is used by Modelity for validation and serialization.
    This interface is designed to handle the full range of JSON-compatible
    types, with additional support for special values like
    :obj:`modelity.unset.Unset` and unknown types.

    Type descriptors are responsible for narrowing or coercing input values to
    determine the most appropriate visit method. For example, a date or time
    object might be converted to a string and then passed to
    :meth:`visit_string`.

    .. versionadded:: 0.17.0

    .. versionchanged:: 0.21.0

        All ``*_begin`` methods can now return ``True`` to skip visiting. For
        example, if :meth:`visit_model_begin` returned ``True``, then model
        visiting is skipped and corresponding :meth:`visit_model_end` will not
        be called. This feature can be used by dump visitors to exclude things
        from the output, or by validation visitors to prevent some validation
        logic from being called.
    """

    @abc.abstractmethod
    def visit_model_begin(self, loc: Loc, value: Any) -> Optional[bool]:
        """Start visiting a model object.

        :param loc:
            The location of the value being visited.

        :param value:
            The object to visit.
        """

    @abc.abstractmethod
    def visit_model_end(self, loc: Loc, value: Any):
        """Finish visiting a model object.

        :param loc:
            The location of the value being visited.

        :param value:
            The visited object.
        """

    @abc.abstractmethod
    def visit_mapping_begin(self, loc: Loc, value: Mapping) -> Optional[bool]:
        """Start visiting a mapping object.

        :param loc:
            The location of the value being visited.

        :param value:
            The object to visit.
        """

    @abc.abstractmethod
    def visit_mapping_end(self, loc: Loc, value: Mapping):
        """Finish visiting a mapping object.

        :param loc:
            The location of the value being visited.

        :param value:
            The visited object.
        """

    @abc.abstractmethod
    def visit_sequence_begin(self, loc: Loc, value: Sequence) -> Optional[bool]:
        """Start visiting a sequence object.

        :param loc:
            The location of the value being visited.

        :param value:
            The object to visit.
        """

    @abc.abstractmethod
    def visit_sequence_end(self, loc: Loc, value: Sequence):
        """Finish visiting a sequence object.

        :param loc:
            The location of the value being visited.

        :param value:
            The visited object.
        """

    @abc.abstractmethod
    def visit_set_begin(self, loc: Loc, value: Set) -> Optional[bool]:
        """Start visiting a set object.

        :param loc:
            The location of the value being visited.

        :param value:
            The object to visit.
        """

    @abc.abstractmethod
    def visit_set_end(self, loc: Loc, value: Set):
        """Finish visiting a set object.

        :param loc:
            The location of the value being visited.

        :param value:
            The visited object..
        """

    @abc.abstractmethod
    def visit_supports_validate_begin(self, loc: Loc, value: Any) -> Optional[bool]:
        """Start visiting a type supporting per-type validation.

        This will be called by type descriptors that implement
        :class:`ISupportsValidate` interface.

        :param loc:
            The location of the value being visited.

        :param value:
            The object to visit.
        """

    @abc.abstractmethod
    def visit_supports_validate_end(self, loc: Loc, value: Any):
        """Finish visiting a type supporting per-type validation.

        :param loc:
            The location of the value being visited.

        :param value:
            The visited object.
        """

    @abc.abstractmethod
    def visit_string(self, loc: Loc, value: str):
        """Visit a string value.

        :param loc:
            The location of the value being visited.

        :param value:
            The value to visit.
        """

    @abc.abstractmethod
    def visit_bool(self, loc: Loc, value: bool):
        """Visit a boolean value.

        :param loc:
            The location of the value being visited.

        :param value:
            The value to visit.
        """

    @abc.abstractmethod
    def visit_number(self, loc: Loc, value: Number):
        """Visit a number value.

        :param loc:
            The location of the value being visited.

        :param value:
            The value to visit.
        """

    @abc.abstractmethod
    def visit_none(self, loc: Loc, value: None):
        """Visit a ``None`` value.

        :param loc:
            The location of the value being visited.

        :param value:
            The value to visit.
        """

    @abc.abstractmethod
    def visit_unset(self, loc: Loc, value: UnsetType):
        """Visit an :obj:`modelity.unset.Unset` value.

        :param loc:
            The location of the value being visited.

        :param value:
            The value to visit.
        """

    @abc.abstractmethod
    def visit_any(self, loc: Loc, value: Any):
        """Visit any value.

        This method will be called when the type is unknown or when the type
        did not match any of the other visit methods.

        :param loc:
            The location of the value being visited.

        :param value:
            The value or object to visit.
        """
