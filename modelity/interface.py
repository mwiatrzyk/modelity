import abc
from numbers import Number
from types import NoneType
from typing import Any, Mapping, Optional, Protocol, Sequence, Set, Union, TypeVar, Generic

from modelity.error import Error
from modelity.loc import Loc
from modelity.unset import UnsetType

T = TypeVar("T")


#: A sentinel value indicating that the return value or the input arguments
#: should be discarded by the caller.
#:
#: Currently used only by the :meth:`IDumpFilter.__call__` method.
DISCARD = object()


class IField(Protocol):
    """Protocol describing single model field."""

    #: Type descriptor for this field.
    descriptor: "ITypeDescriptor"

    #: Flag telling if this field is optional (``True``) or required (``False``)
    optional: bool


class IModel(Protocol):
    """Protocol describing common interface for data models.

    This interface is implicitly implemented by :class:`modelity.model.Model`
    class.
    """

    #: The root location of this model.
    #:
    #: If the model is located inside some outer model, then this will point to
    #: a field where this model instance is currently located.
    __loc__: Loc

    #: Mapping with field definitions for this model.
    __model_fields__: Mapping[str, IField]

    #: List of hooks declared for this model.
    __model_hooks__: list["IBaseHook"]

    def accept(self, visitor: "IModelVisitor"):
        """Accept visitor on this model.

        :param visitor:
            The visitor to use.
        """


class IBaseHook(Protocol):
    """Base class for hook protocols."""

    #: The ID number assigned for a hook.
    #:
    #: This is sequential number that can be used to order hooks in their
    #: declaration order.
    __modelity_hook_id__: int

    #: The name of a hook.
    #:
    #: Modelity uses this to group hooks by their functionality.
    __modelity_hook_name__: str


class IModelHook(IBaseHook):
    """Base class for hooks operating on entire models.

    .. versionadded:: 0.16.0
    """


class IFieldHook(IBaseHook):
    """Base class for hooks operating on selected model fields.

    .. versionadded:: 0.16.0
    """

    #: Set containing field names this hook will be applied to.
    #:
    #: If this is an empty set, then the hook will be applied to all fields of
    #: the model where it was declared.
    __modelity_hook_field_names__: set[str]


class IModelValidationHook(IModelHook):
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


class IModelPrevalidationHook(IModelValidationHook):
    """Interface for hooks that are run just after the validation has started.

    .. versionadded:: 0.16.0
    """

    __modelity_hook_name__ = "model_prevalidator"


class IModelPostvalidationHook(IModelValidationHook):
    """Interface for hooks that are run just before validation ends.

    .. versionadded:: 0.16.0
    """

    __modelity_hook_name__ = "model_postvalidator"


class IFieldValidationHook(IFieldHook):
    """Interface of the field-level validation hooks.

    Field validators are executed for selected fields and only if those fields
    have values set.
    """

    __modelity_hook_name__ = "field_validator"

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


class IFieldPreprocessingHook(IFieldHook):
    """Protocol specifying interface of the field-level preprocessing hooks.

    Preprocessing is performed separately for each field that is set or
    modified and always before type parsing stage. The role of preprocessing
    hooks is to filter input data before it gets passed to the parsing stage.
    Preprocessors cannot access model object or other fields.
    """

    __modelity_hook_name__ = "field_preprocessor"

    def __call__(_, cls: type[IModel], errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
        """Call field's preprocessing hook.

        :param cls:
            Model's type.

        :param errors:
            List of errors.

            Can be modified by the hook if the hook fails.

        :param loc:
            The location of the currently processed field.

        :param value:
            The processed value of any type.
        """


class IFieldPostprocessingHook(IFieldHook):
    """Protocol specifying interface of the field-level postprocessing hooks.

    Postprocessing stage is executed after successful preprocessing and type
    parsing stages. First postprocessor in a chain is guaranteed to receive the
    value of a correct type, so no double checks are needed. If more
    postprocessors are defined, then N-th postprocessor receives value returned
    by (N-1)-th postprocessor. Unlike preprocessors, postprocessors can access
    model instance and other fields but unlike for field validators the model
    may not be fully initialized yet and this must be taken into account when
    using this feature.

    .. note::
        Modelity guarantees that the fields are constructed in same order as
        the declaration goes in the model class.

    .. important::
        There are no more checks after postprocessing stage, so theoretically
        postprocessor are able to change value type to something other than
        declared in the model. It is important to always return a value from
        postprocessor and it is highly recommended to not change its type, as
        it may break some of the built-in functionalities that depend on field
        type.
    """

    __modelity_hook_name__ = "field_postprocessor"

    def __call__(
        _, cls: type[IModel], self: IModel, errors: list[Error], loc: Loc, value: Any
    ) -> Union[Any, UnsetType]:
        """Call field's postprocessing hook.

        :param cls:
            Model's type this hook was declared in.

        :param self:
            Model's instance this hook runs for.

        :param errors:
            List of errors.

            Can be modified by the hook.

        :param loc:
            The location of the currently processed field.

        :param value:
            The value to process.
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
    def validate(self, errors: list[Error], loc: Loc, value: T):
        """Validate value of type *T*.

        This method should be used for types that have to be additionally
        verified when model is validated. For example, if model's field is
        mutable and has constraints provided, those constraints will have to be
        rerun during model validation. If particular type does not need that
        kind of additional verification, then implementation of this method
        should be empty.

        :param errors:
            Mutable list of errors.

        :param loc:
            The location of the *value* inside the model.

        :param value:
            The value to validate.

            It is guaranteed to be an instance of type *T*.
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


class ITypeDescriptorFactory(Protocol):
    """Protocol describing type descriptor factory function.

    These functions are used to create instances of :class:`ITypeDescriptor`
    for provided type and type options.
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
    """

    @abc.abstractmethod
    def visit_model_begin(self, loc: Loc, value: IModel):
        """Start visiting a model object.

        :param loc:
            The location of the value being visited.

        :param value:
            The object to visit.
        """

    @abc.abstractmethod
    def visit_model_end(self, loc: Loc, value: IModel):
        """Finish visiting a model object.

        :param loc:
            The location of the value being visited.

        :param value:
            The object to visit.
        """

    @abc.abstractmethod
    def visit_mapping_begin(self, loc: Loc, value: Mapping):
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
            The object to visit.
        """

    @abc.abstractmethod
    def visit_sequence_begin(self, loc: Loc, value: Sequence):
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
            The object to visit.
        """

    @abc.abstractmethod
    def visit_set_begin(self, loc: Loc, value: Set):
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
            The object to visit.
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
    def visit_none(self, loc: Loc, value: NoneType):
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
