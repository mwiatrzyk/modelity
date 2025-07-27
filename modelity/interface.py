import abc
from numbers import Number
from typing import Any, Iterator, Mapping, Protocol, Sequence, Set, Union, TypeVar, Generic

from modelity import _utils
from modelity.error import Error
from modelity.loc import Loc
from modelity.unset import UnsetType

__all__ = export = _utils.ExportList()  # type: ignore

T = TypeVar("T")


@export
class IField(Protocol):
    """Protocol describing single model field."""

    #: Field's name.
    name: str

    #: Field's type annotation.
    typ: Any

    #: Type descriptor for this field.
    descriptor: "ITypeDescriptor"

    #: Flag telling if this field is optional (``True``) or required (``False``)
    optional: bool


@export
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

    # #: Mapping with field definitions for this model.
    __model_fields__: Mapping[str, IField]

    # #: List of hooks declared for this model.
    __model_hooks__: Sequence["IModelHook"]

    def __iter__(self) -> Iterator[str]:
        """Iterate over names of fields that have value assigned."""
        ...

    def accept(self, visitor: "IModelVisitor"):
        """Accept visitor on this model.

        :param visitor:
            The visitor to use.
        """
        ...


@export
class IModelHook(Protocol):
    """Protocol describing base interface for model hooks.

    Hooks are used to wrap user-defined functions and use them to inject extra
    logic to either parsing or validation stages of data processing.
    """

    #: The sequential ID number assigned for this hook.
    #:
    #: This is used to sort hooks by their declaration order when they are
    #: collected from the model.
    __modelity_hook_id__: int

    #: The name of this hook.
    __modelity_hook_name__: str


@export
class IModelValidationHook(IModelHook):
    """Protocol describing interface of the model validation hooks."""

    @abc.abstractmethod
    def __call__(_, cls: type[IModel], self: IModel, root: IModel, ctx: Any, errors: list[Error], loc: Loc):
        pass


@export
class IModelFieldHook(IModelHook):
    """Subclass of :class:`IModelHook` to be used as a base for hooks that
    operate on field level rather than entire model.

    For instance, hooks of this type will be executed for selected fields only
    when the field is set, modified or validated (depending on the hook
    type).
    """

    #: Set containing names of fields this hook will be applied to.
    #:
    #: If this set is empty, then hook will be applied for all fields.
    __modelity_hook_field_names__: set[str]


@export
class IFieldPreprocessingHook(IModelFieldHook):
    """Base class for user-defined preprocessing hooks.

    Preprocessing is optional and first stage of data processing, executed when
    field in a model is either set or modified. The role of preprocessors is to
    prepare data for further stages Preprocessors cannot access model instance
    and other fields.
    """

    @abc.abstractmethod
    def __call__(self, cls: type[IModel], errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
        """Invoke the hook.

        Returned value will be passed to the next preprocessing hook (if any)
        or to the field's value parser. If preprocessing failed, then
        :obj:`modelity.unset.Unset` should be returned and error should be
        added to the *errors* list.

        :param cls:
            Model type this hook runs for.

        :param errors:
            Mutable list of errors.

        :param loc:
            The location of the field being processed.

        :param value:
            The value to be preprocessed.
        """


@export
class IFieldPostprocessingHook(IModelFieldHook):
    """Base class for user-defined postprocessing hooks.

    Postprocessing is optional and last stage of data processing, executed
    after successful parsing of the input data to a type field is expecting.
    The role of postprocessors is to perform some additional field-specific
    validation that must be executed every time the field is changed. In
    addition, postprocessors can also be used to modify the data before it is
    stored in the model. Postprocessors can access model instance and other
    fields for as long as the currently postprocessed field is declared
    **after** the field that is accessed.
    """

    @abc.abstractmethod
    def __call__(
        _, cls: type[IModel], self: IModel, errors: list[Error], loc: Loc, value: Any
    ) -> Union[Any, UnsetType]:
        """Invoke the hook.

        Returned value will either be passed to a next postprocessing hook (if
        any) or stored as field's final value in the model. If postprocessor
        fails then :obj:`modelity.unset.Unset` object should be returned and
        error added to the *errors* list.

        :param cls:
            Model type this hook runs for.

        :param self_:
            Model instance.

            Postprocessor can use this to access other fields, but fields
            declared after the one being postprocessed may not have values
            assigned yet.

        :param errors:
            Mutable list of errors.

        :param loc:
            The location of the field being postprocessed.

        :param value:
            The value from parsing stage or previous postprocessor.
        """


@export
class IFieldValidationHook(IModelFieldHook):

    @abc.abstractmethod
    def __call__(_, cls: type[IModel], self: IModel, root: IModel, ctx: Any, errors: list[Error], loc: Loc, value: Any):
        pass


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
            The visited object.
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
            The visited object.
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
            The visited object.
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
            The visited object..
        """

    @abc.abstractmethod
    def visit_supports_validate_begin(self, loc: Loc, value: Any):
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
