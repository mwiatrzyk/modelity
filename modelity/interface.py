import abc
from numbers import Number
from typing import Any, Mapping, Optional, Protocol, Sequence, Set, Union

from modelity import _utils
from modelity.error import Error
from modelity.loc import Loc
from modelity.unset import UnsetType

__all__ = export = _utils.ExportList()  # type: ignore


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
        """Invoke this hook.

        The actual parameters and type of return value depends on hook type.
        Check :mod:`modelity.hooks` for more details.
        """
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
class ITypeDescriptor(abc.ABC):
    """Abstract base class for type descriptors.

    This interface is used by Modelity to invoke type-specific parsing and
    visitor accepting logic. Type descriptors are created by model metaclass
    when model type is declared, and later these descriptors are reused by each
    model instance to perform parsing, validation and dumping operations. Type
    descriptors can also trigger another type descriptors and this is how
    Modelity implements complex types, like `dict[str, int]`.

    This is also an entry point for user-defined types; check
    :func:`modelity.hooks.type_descriptor_factory` hook for more details.
    """

    @abc.abstractmethod
    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
        """Parse given *value* into new instance of type represented by this
        type descriptor.

        Should return parsed value, or :obj:`modelity.unset.Unset` object if
        parsing failed. When ``Unset`` is returned, new errors should also be
        added to *errors* list to inform why parsing has failed.

        :param errors:
            List of errors.

        :param loc:
            The location of the *value* inside the model.

        :param value:
            The value to parse.
        """

    @abc.abstractmethod
    def accept(self, visitor: "IModelVisitor", loc: Loc, value: Any):
        """Accept given model visitor.

        This method is meant to provide visitor accepting logic for a type that
        is being represented by this type descriptor. For example, for numeric
        types you should call
        :meth:`modelity.interface.IModelVisitor.visit_number`. The rule of
        thumb is to use the best possible ``visit_*`` method, or sequence of
        methods (for complex types).

        :param visitor:
            The visitor to accept.

        :param loc:
            The location of the value inside model.

        :param value:
            The value to process.

            This will always be the output of successful :meth:`parse` call,
            yet it may get modified by postprocessing hooks (if any).
        """


@export
class IValidatableTypeDescriptor(ITypeDescriptor):
    """Abstract base class for type descriptors that need to provide additional
    type-specific validation of their instances.

    When this abstract class is used as a base for type descriptor, then
    :meth:`validate` will be called when model is validated, contributing to
    built-in validators.

    As an example, type descriptor for :obj:`typing.Annotated` wrapper was
    implemented as a subclass of this interface, allowing constraints to be
    verified when field is modified and again when model is validated.
    """

    @abc.abstractmethod
    def validate(self, errors: list[Error], loc: Loc, value: Any):
        """Validate instance of type represented by this type descriptor.

        When validation fails, then *errors* should be populated with new
        errors that were found. Otherwise *errors* should be left intact.

        :param errors:
            Mutable list of errors.

        :param loc:
            The location of the *value* inside the model.

        :param value:
            The value to validate.
        """


@export
class ITypeDescriptorFactory(Protocol):
    """Protocol describing type descriptor factories.

    These functions are used to create instances of :class:`ITypeDescriptor`
    for provided type and type options.

    .. versionchanged:: 0.17.0
        This protocol was made generic.
    """

    def __call__(self, typ: Any, type_opts: dict) -> ITypeDescriptor:
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
