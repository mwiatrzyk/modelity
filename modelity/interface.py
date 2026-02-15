import abc
from typing import Any, Mapping, Optional, Protocol, Sequence, Set, Union

from modelity import _utils
from modelity.error import Error
from modelity.loc import Loc
from modelity.unset import UnsetType

__all__ = export = _utils.ExportList()  # type: ignore


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
class IField(Protocol):
    """Protocol describing public interface of model fields.

    .. versionadded:: 0.31.0
    """

    #: The type annotation set for this field.
    typ: Any

    #: The type descriptor assigned for this field.
    descriptor: ITypeDescriptor

    #: Flag indicating whether this field is optional.
    #:
    #: A field is optional if it accepts ``None``, ``Unset``, or both as valid
    #: values during parsing and validation. Modelity supports the following
    #: markers for optional fields:
    #:
    #: * :obj:`typing.Optional`
    #: * :obj:`modelity.types.StrictOptional`
    #: * :obj:`modelity.types.LooseOptional`
    #:
    #: .. versionadded:: 0.35.0
    optional: bool

    #: Flag indicating whether this field is optional that accepts
    #: :obj:`modelity.unset.Unset` as a valid value during validation step.
    #:
    #: This will never be ``True`` for required fields.
    #:
    #: .. versionadded:: 0.35.0
    #:      Replaced ``is_unsettable()`` used earlier.
    unsettable: bool

    #: Flag indicating whether this field is deferred.
    #:
    #: Deferred fields allow ``Unset`` as valid values during parsing, but the
    #: field must be set later to allow successful validation. To mark a field as
    #: deferred, use :obj:`modelity.types.Deferred` marker.
    #:
    #: This is used for fields that are meant to be initialized later.
    #:
    #: .. versionadded:: 0.35.0
    deferred: bool

    def compute_default(self) -> Any:
        ...


@export
class IModel(Protocol):
    """Protocol describing public interface of model objects.

    .. versionadded:: 0.31.0
    """

    def accept(self, visitor: "IModelVisitor", loc: Loc):
        """Accept provided model visitor.

        :param visitor:
            The visitor to accept.

        :param loc:
            The visited location of the model.

            For root model this will be empty location. For nested model this
            will be location pointing to the model's location inside outer
            model.
        """
        ...


@export
class IModelVisitor(Protocol):
    """Base class for model data visitors.

    This mechanism allows to traverse through Modelity models in a
    deterministric way and, depending on the implementation, serialize or
    validate it.

    .. versionchanged:: 0.31.0

        Methods ``visit_string``, ``visit_number``, ``visit_bool`` and are now
        all merged into single :meth:`visit_scalar` method. This allows to pass
        original values to visitors and let them decide what to do next.

    .. versionchanged:: 0.28.0

        Now uses structural typing based on :class:`typing.Protocol` instead of
        :class:`abc.ABC`. This allows nicer implementations of visitor wrappers
        at the cost of having to remember all the methods needed.

    .. versionchanged:: 0.21.0

        All ``*_begin`` methods can now return ``True`` to skip visiting. For
        example, if :meth:`visit_model_begin` returned ``True``, then model
        visiting is skipped and corresponding :meth:`visit_model_end` will not
        be called. This feature can be used by dump visitors to exclude things
        from the output, or by validation visitors to prevent some validation
        logic from being called.

    .. versionadded:: 0.17.0
    """

    def visit_model_begin(self, loc: Loc, value: IModel) -> Optional[bool]:
        """Start visiting model object.

        :param loc:
            The location of the visited model.

        :param value:
            The visited model object.
        """
        ...

    def visit_model_end(self, loc: Loc, value: IModel):
        """Finish visiting model object.

        :param loc:
            The location of the visited model.

        :param value:
            The visited model object.
        """
        ...

    def visit_model_field_begin(self, loc: Loc, value: Any, field: IField) -> Optional[bool]:
        """Start visiting model field.

        This is called for every field in a model no matter if the field is set
        or not.

        :param loc:
            The location of the visited value.

        :param value:
            The visited field value.

        :param field:
            The visited field metadata.
        """
        ...

    def visit_model_field_end(self, loc: Loc, value: Any, field: IField):
        """Finish visiting model field.

        :param loc:
            The location of the visited value.

        :param value:
            The visited field value.

        :param field:
            The visited field metadata.
        """
        ...

    def visit_mapping_begin(self, loc: Loc, value: Mapping) -> Optional[bool]:
        """Start visiting a mapping object.

        :param loc:
            The location of the visited mapping object.

        :param value:
            The visited mapping object.
        """
        ...

    def visit_mapping_end(self, loc: Loc, value: Mapping):
        """Finish visiting a mapping object.

        :param loc:
            The location of the visited mapping object.

        :param value:
            The visited mapping object.
        """
        ...

    def visit_sequence_begin(self, loc: Loc, value: Sequence) -> Optional[bool]:
        """Start visiting a sequence object.

        :param loc:
            The location of the visited sequence object.

        :param value:
            The visited sequence object.
        """
        ...

    def visit_sequence_end(self, loc: Loc, value: Sequence):
        """Finish visiting a sequence object.

        :param loc:
            The location of the visited sequence object.

        :param value:
            The visited sequence object.
        """
        ...

    def visit_set_begin(self, loc: Loc, value: Set) -> Optional[bool]:
        """Start visiting a set object.

        :param loc:
            The location of the visited set object.

        :param value:
            The visited set object.
        """
        ...

    def visit_set_end(self, loc: Loc, value: Set):
        """Finish visiting a set object.

        :param loc:
            The location of the visited set object.

        :param value:
            The visited set object.
        """
        ...

    def visit_none(self, loc: Loc, value: None):
        """Visit a ``None`` value.

        Called when :obj:`None` object is found.

        :param loc:
            The location of the visited value.

        :param value:
            The visited value.
        """
        ...

    def visit_unset(self, loc: Loc, value: UnsetType):
        """Visit an ``Unset`` value.

        Called when :obj:`modelity.unset.Unset` object is found.

        :param loc:
            The location of the visited value.

        :param value:
            The visited value.
        """
        ...

    def visit_scalar(self, loc: Loc, value: Any):
        """Visit scalar object.

        Scalars are primitive objects that are neither containers, nor model
        objects. All Python primitive types (ints, floats, strings, booleans,
        enums, datetimes etc.) are scalars from the Modelity point of view.

        :param loc:
            The location of the visited value.

        :param value:
            The visited value.
        """
        ...

    def visit_any(self, loc: Loc, value: Any):
        """Visit any value.

        This is called for values from untyped containers, fields marked with
        :obj:`typing.Any` or typed containers where :obj:`typing.Any` is used
        as a type hint.

        This method, unlike :meth:`visit_scalar`, can also be called with
        elements that are containers, not scalars.

        Implementations are responsible for deciding whether to recurse into
        the value if it is a container.

        :param loc:
            The location of the visited value.

        :param value:
            The visited value.
        """
        ...
