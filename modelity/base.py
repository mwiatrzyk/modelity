import abc
import copy
import dataclasses
from typing import Any, Callable, ClassVar, Iterator, Mapping, Optional, Protocol, Sequence, Set, TypeVar, Union, cast

import typing_extensions

from modelity import _export_list, _utils
from modelity._internal import hooks as _int_hooks
from modelity.exc import ParsingError
from modelity.typing import is_any_optional, is_deferred, is_unsettable

from .loc import Loc
from .error import Error, ErrorFactory
from .unset import Unset, UnsetType

__all__ = export = _export_list.ExportList(["register_type_handler_factory", "create_type_handler"])  # type: ignore

T = TypeVar("T")

_IGNORED_FIELD_NAMES = {
    "__model_fields__",
}


@export
class TypeHandler(abc.ABC):
    """Base class for type handlers.

    Type handlers are used by Modelity to provide type-specific runtime logic
    to models. Type handlers are constructed from type object or type
    annotations when model type is created and then used by model instances to
    handle user data.

    .. versionadded:: 0.36.0
        Replaced ``modelity.interface.ITypeDescriptor`` used earlier.
    """

    @abc.abstractmethod
    def parse(self, errors: list[Error], loc: Loc, value: Any, /) -> Union[Any, UnsetType]:
        """Parse given value as instance of handled type.

        Successful parsing must return instance of handled type, which can be
        unchanged *value* if it already has desired type.

        Failure must be reported by one or more errors added to *errors* list,
        and :obj:`modelity.unset.Unset` value returned.

        :param errors:
            Mutable list of errors.

        :param loc:
            The current location in the model.

        :param value:
            The input value.
        """

    @abc.abstractmethod
    def accept(self, visitor: "ModelVisitor", loc: Loc, value: Any, /):
        """Accept given model visitor.

        This method is meant to provide visitor accepting logic for handled
        type. Basically, this method will call the most adequate visitor
        method, or (for complex types) sequence of visitor methods. See
        :class:`ModelVisitor` for more details.

        :param visitor:
            The visitor to accept.

        :param loc:
            The visited location in the model.

        :param value:
            The value to process.

            It can be assumed that this value has the right type already.
        """


@export
class TypeHandlerFactory(Protocol):
    """Protocol describing type handler factories.

    .. versionadded::
        Replaced ``modelity.interface.ITypeDescriptorFactory`` used earlier.
    """

    def __call__(self, typ: Any, /, **type_opts) -> TypeHandler:
        """Create a type handler for the provided type and options.

        :param typ:
            The type or special form to create a handler for.

        :param type_opts:
            Optional type-specific options passed to the handler.
        """
        ...


@export
class Constraint(abc.ABC):
    """Base class for constraints.

    Constraints are used to define parsing- and validation-time criteria that
    must be met for successful parsing/validation. Instances of this base class
    are used with types wrapped with :obj:`typing.Annotated`.

    .. versionadded:: 0.36.0
        Replaced ``modelity.interface.IConstraint`` used earlier.
    """

    @abc.abstractmethod
    def __repr__(self) -> str:
        """Return text representation of the constraint.

        This is used when rendering constraints in error messages.
        """

    @abc.abstractmethod
    def __call__(self, errors: list[Error], loc: Loc, value: Any) -> bool:
        """Run all checks against given value.

        Returns True and does not modify error list if value satisfies the
        constraint.

        Returns False and adds one or more errors to error list if value does
        not satisfy the constraint.

        :param errors:
            Mutable list of errors.

        :param loc:
            The current location in the model.

        :param value:
            The validated value.
        """


@export
class TypeHandlerWithValidation(TypeHandler):
    """Base class for type handlers that need to run additional type-specific
    validation when model is validated.

    For example, this base class is used by type handler for
    :obj:`typing.Annotated` types to ensure that constraints are still
    satisfied when model is validated, which is impossible to ensure only
    during parsing stage for mutable types.

    .. versionadded:: 0.36.0
        Replaced ``modelity.interface.IValidatableTypeDescriptor`` used earlier.
    """

    @abc.abstractmethod
    def validate(self, errors: list[Error], loc: Loc, value: Any) -> bool:
        """Validate the value.

        Returns True and does not modify error list if the value is valid.

        Returns False and adds one or more errors to the errors list if the
        value is not valid.

        :param errors:
            Mutable list of errors.

        :param loc:
            The current location in the model.

        :param value:
            The validated value.
        """


@export
class ModelVisitor(abc.ABC):
    """Base class for model data visitors.

    This mechanism allows to traverse through Modelity models in a
    deterministic way and, depending on the implementation, serialize or
    validate it.

    .. versionadded:: 0.36.0
        Replaced ``modelity.interface.IModelVisitor`` used earlier.
    """

    @abc.abstractmethod
    def visit_model_begin(self, loc: Loc, value: "Model") -> Optional[bool]:  # TODO: use sentinel
        """Start visiting model object.

        :param loc:
            The location of the visited model.

        :param value:
            The visited model object.
        """
        ...

    @abc.abstractmethod
    def visit_model_end(self, loc: Loc, value: "Model"):
        """Finish visiting model object.

        :param loc:
            The location of the visited model.

        :param value:
            The visited model object.
        """
        ...

    @abc.abstractmethod
    def visit_model_field_begin(self, loc: Loc, value: Any, field: "Field") -> Optional[bool]:  # TODO: use sentinel
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

    @abc.abstractmethod
    def visit_model_field_end(self, loc: Loc, value: Any, field: "Field"):
        """Finish visiting model field.

        :param loc:
            The location of the visited value.

        :param value:
            The visited field value.

        :param field:
            The visited field metadata.
        """
        ...

    @abc.abstractmethod
    def visit_mapping_begin(self, loc: Loc, value: Mapping) -> Optional[bool]:  # TODO: use sentinel
        """Start visiting a mapping object.

        :param loc:
            The location of the visited mapping object.

        :param value:
            The visited mapping object.
        """
        ...

    @abc.abstractmethod
    def visit_mapping_end(self, loc: Loc, value: Mapping):
        """Finish visiting a mapping object.

        :param loc:
            The location of the visited mapping object.

        :param value:
            The visited mapping object.
        """
        ...

    @abc.abstractmethod
    def visit_sequence_begin(self, loc: Loc, value: Sequence) -> Optional[bool]:  # TODO: use sentinel
        """Start visiting a sequence object.

        :param loc:
            The location of the visited sequence object.

        :param value:
            The visited sequence object.
        """
        ...

    @abc.abstractmethod
    def visit_sequence_end(self, loc: Loc, value: Sequence):
        """Finish visiting a sequence object.

        :param loc:
            The location of the visited sequence object.

        :param value:
            The visited sequence object.
        """
        ...

    @abc.abstractmethod
    def visit_set_begin(self, loc: Loc, value: Set) -> Optional[bool]:  # TODO: use sentinel
        """Start visiting a set object.

        :param loc:
            The location of the visited set object.

        :param value:
            The visited set object.
        """
        ...

    @abc.abstractmethod
    def visit_set_end(self, loc: Loc, value: Set):
        """Finish visiting a set object.

        :param loc:
            The location of the visited set object.

        :param value:
            The visited set object.
        """
        ...

    @abc.abstractmethod
    def visit_none(self, loc: Loc, value: None):
        """Visit a ``None`` value.

        Called when :obj:`None` object is found.

        :param loc:
            The location of the visited value.

        :param value:
            The visited value.
        """
        ...

    @abc.abstractmethod
    def visit_unset(self, loc: Loc, value: UnsetType):
        """Visit an ``Unset`` value.

        Called when :obj:`modelity.unset.Unset` object is found.

        :param loc:
            The location of the visited value.

        :param value:
            The visited value.
        """
        ...

    @abc.abstractmethod
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

    @abc.abstractmethod
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


@export
def field_info(
    *,
    default: Union[T, UnsetType] = Unset,
    default_factory: Union[Callable[[], T], UnsetType] = Unset,
    title: Optional[str] = None,
    description: Optional[str] = None,
    examples: Optional[list] = None,
    **type_opts,
) -> T:
    """Helper for creating :class:`FieldInfo` objects in a way that will
    satisfy code linters.

    Check :class:`FieldInfo` class documentation to get help on available
    parameters.

    .. versionchanged:: 0.19.0

        Added *title*, *description* and *examples* parameters.

    .. versionadded:: 0.16.0
    """
    return cast(
        T,
        FieldInfo(
            default=default,
            default_factory=default_factory,
            title=title,
            description=description,
            examples=examples,
            type_opts=type_opts,
        ),
    )


@export
@dataclasses.dataclass
class FieldInfo:
    """Class for setting field metadata."""

    #: Default field value.
    default: Any = Unset

    #: Default value factory function.
    #:
    #: Allows to create default values that are evaluated each time the model
    #: is created, and therefore producing different default values for
    #: different model instances.
    default_factory: Union[Callable[[], Any], UnsetType] = Unset  # type: ignore

    #: The title of this field.
    #:
    #: This should be relatively short.
    #:
    #: .. versionadded:: 0.19.0
    title: Optional[str] = None

    #: The description of this field.
    #:
    #: This is a long description, to be used when :attr:`title` is not
    #: sufficient.
    #:
    #: .. versionadded:: 0.19.0
    description: Optional[str] = None

    #: The example values for this field.
    #:
    #: This is not used directly in any way by the library, but 3rd party tools
    #: may use it f.e. to create random valid objects for tests.
    #:
    #: .. versionadded:: 0.19.0
    examples: Optional[list] = None

    #: Additional options for type descriptors.
    #:
    #: This can be used to pass additional type-specific settings, like
    #: input/output formats and more. The actual use of these options depends
    #: on the field type.
    type_opts: dict = dataclasses.field(default_factory=dict)


@export
@dataclasses.dataclass
class Field:
    """Field created from annotation.

    This class implicitly implements :class:`modelity.interface.IField`
    protocol.
    """

    #: Field's name.
    #:
    #: This is the name of a field used in a model.
    name: str

    #: Field's type.
    #:
    #: This is type annotation used to declare a field in a model.
    typ: Any

    #: Field's type handler.
    #:
    #: This is assigned when model type is created and is used during model
    #: construction to parse input values into model-defined types.
    type_handler: TypeHandler

    _: dataclasses.KW_ONLY

    #: Field's user-defined info object.
    field_info: Optional[FieldInfo] = None

    #: See :attr:`modelity.interface.IField.optional`.
    optional: bool = False

    #: See :attr:`modelity.interface.IField.unsettable`.
    unsettable: bool = False

    #: See :attr:`modelity.interface.IField.deferred`.
    deferred: bool = False

    @property
    def required(self) -> bool:
        """Flag indicating whether this field is required during parsing.

        A model with required field will fail parsing if the field is not
        provided to model constructor and does not have default value set.
        Any field that is neither optional nor deferred is required.

        .. versionadded:: 0.35.0
        """
        return not self.optional and not self.deferred

    def has_default(self) -> bool:
        """Check if this field has default value set.

        .. versionadded:: 0.16.0
        """
        if self.field_info is None:
            return False
        return self.field_info.default is not Unset or self.field_info.default_factory is not Unset

    def compute_default(self) -> Union[Any, UnsetType]:
        """Compute default value for this field."""
        if self.field_info is None:
            return Unset
        default = self.field_info.default
        default_factory = self.field_info.default_factory
        if default is Unset and default_factory is Unset:
            return Unset
        elif default is not Unset:
            if not _utils.is_mutable(default):
                return default
            return copy.deepcopy(default)
        elif callable(default_factory):
            return default_factory()
        else:
            return Unset


@export
class ModelMeta(type):
    """Metaclass for models.

    The role of this metaclass is to provide field initialization, type
    descriptor lookup and inheritance handling.

    It is used as a metaclass by :class:`Model` base class and all methods and
    properties it provides can be accessed via ``__class__`` attribute of the
    :class:`Model` class instances.
    """

    #: Mapping containing all fields declared for a model.
    #:
    #: The name of a field is used as a key, while :class:`Field` class
    #: instance is used as a value. The order reflects order of annotations in
    #: the created model class.
    __model_fields__: Mapping[str, Field]

    def __new__(cls, name: str, bases: tuple, attrs: dict):
        attrs["__model_fields__"] = fields = dict[str, Field]()
        attrs["_modelity_hooks"] = hooks = list[_int_hooks.IBaseHook]()
        for base in bases:
            fields.update(getattr(base, "__model_fields__", {}))
            modelity_hooks = getattr(base, "_modelity_hooks", None)
            if modelity_hooks is not None:
                hooks.extend(modelity_hooks)
            else:
                hooks.extend(_collect_hooks_from_mixin_class(base))
        for key in dict(attrs):
            attr_value = attrs[key]
            if _int_hooks.is_base_hook(attr_value):
                hooks.append(attr_value)
                del attrs[key]
        hooks.sort(key=lambda x: x.__modelity_hook_id__)
        annotations = attrs.pop("__annotations__", {})
        for field_name, annotation in annotations.items():
            if field_name in _IGNORED_FIELD_NAMES:
                continue
            field_info = attrs.pop(field_name, Unset)
            if not isinstance(field_info, FieldInfo):
                field_info = FieldInfo(default=field_info)
            optional = is_any_optional(annotation)
            bound_field = Field(
                field_name,
                annotation,
                create_type_handler(annotation, **field_info.type_opts),
                field_info=field_info,
                optional=optional,
                unsettable=is_unsettable(annotation) if optional else False,
                deferred=is_deferred(annotation) if not optional else False,
            )
            fields[field_name] = bound_field
        attrs["__slots__"] = tuple(fields) + tuple(attrs.get("__slots__", []))
        return super().__new__(cls, name, bases, attrs)


@export
@typing_extensions.dataclass_transform(kw_only_default=True)
class Model(metaclass=ModelMeta):
    """Base class for data models.

    All models created using Modelity must inherit from this base class and
    provide zero or more fields using type annotations in similar way as when
    using Python dataclasses.

    Here's a simple example:

    .. testcode::

        from typing import Optional

        from modelity.api import Model, Deferred, LooseOptional, StrictOptional, Unset, validate

        class Dummy(Model):
            foo: int  # <- required; must be given in constructor
            xyz: float = 3.14  # <- required; optional in constructor, as it has default value set
            bar: Deferred[bool] = Unset  # <- deferred; must be set before validation
            baz: Optional[str] = None  # <- optional; can be `None` but cannot be `Unset`
            spam: LooseOptional[str] = Unset  # <- optional; can be set to `None` or `Unset`
            more_spam: StrictOptional[str] = Unset  # <- optional; can be `Unset` but cannot be `None`

    .. doctest::

        >>> dummy = Dummy(foo='123')  # Construct model instance; Modelity will try to parse input to expected type
        >>> dummy
        Dummy(foo=123, xyz=3.14, bar=Unset, baz=None, spam=Unset, more_spam=Unset)
        >>> validate(dummy)  # Validation will fail; deferred field `bar` is missing
        Traceback (most recent call last):
            ...
        modelity.exc.ValidationError: Found 1 validation error for model 'Dummy':
          bar:
            This field is required [code=modelity.REQUIRED_MISSING]
        >>> dummy.bar = True  # Now let's set a value to `bar` field (models are mutable)
        >>> validate(dummy)  # And now the model is valid
        >>> dummy
        Dummy(foo=123, xyz=3.14, bar=True, baz=None, spam=Unset, more_spam=Unset)
    """

    #: A per-instance view of the :attr:`ModelMeta.__model_fields__` attribute.
    __model_fields__: ClassVar[Mapping[str, Field]]

    def __init__(self, **kwargs) -> None:
        errors: list[Error] = []
        fields = self.__class__.__model_fields__
        for name, field in fields.items():
            value = kwargs.pop(name, Unset)
            if value is Unset:
                value = field.compute_default()
                if value is Unset and not field.optional and not field.deferred:
                    errors.append(ErrorFactory.required_missing(Loc(name)))
            if value is not Unset:
                value = self.__parse(field.type_handler, errors, name, value)
            super().__setattr__(name, value)
        if errors:
            raise ParsingError(self.__class__, tuple(errors))

    def __repr__(self):
        kv = (f"{k}={getattr(self, k)!r}" for k in self.__class__.__model_fields__)
        return f"{self.__class__.__qualname__}({', '.join(kv)})"

    def __eq__(self, value):
        if type(self) is not type(value):
            return NotImplemented
        for k in self.__class__.__model_fields__:
            if getattr(self, k) != getattr(value, k):
                return False
        return True

    def __contains__(self, name):
        return name in self.__class__.__model_fields__ and getattr(self, name) is not Unset

    def __iter__(self):
        for name in self.__class__.__model_fields__.keys():
            if getattr(self, name) is not Unset:
                yield name

    def __parse(
        self, type_handler: TypeHandler, errors: list[Error], field_name: str, value: Any
    ) -> Union[Any, UnsetType]:
        loc = Loc(field_name)
        cls = self.__class__
        value = _run_field_preprocessors(cls, errors, loc, value)  # type: ignore
        if value is Unset:
            return value
        value = type_handler.parse(errors, loc, value)
        if value is Unset:
            return value
        value = _run_field_postprocessors(cls, self, errors, loc, value)  # type: ignore
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        field = self.__class__.__model_fields__.get(name)
        if field is None:
            return super().__setattr__(name, value)
        errors: list[Error] = []
        value = self.__parse(field.type_handler, errors, name, value)
        if errors:
            raise ParsingError(self.__class__, tuple(errors))
        super().__setattr__(name, value)

    def __delattr__(self, name):
        setattr(self, name, Unset)

    def accept(self, visitor: ModelVisitor, loc: Loc):
        """Accept visitor on this model.

        :param visitor:
            The visitor to accept.

        :param loc:
            The location of this model or empty location if this is the root
            model.
        """
        if visitor.visit_model_begin(loc, self) is not True:
            for name, field in self.__class__.__model_fields__.items():
                field_loc = loc + Loc(name)
                value = getattr(self, name)
                if visitor.visit_model_field_begin(field_loc, value, field) is not True:
                    if value is Unset:
                        visitor.visit_unset(field_loc, value)
                    else:
                        field.type_handler.accept(visitor, field_loc, value)
                    visitor.visit_model_field_end(field_loc, value, field)
            visitor.visit_model_end(loc, self)


@export
def register_type_handler_factory(typ: Any, factory: TypeHandlerFactory):
    """Register custom type handler factory for given type.

    This method can be used to register custom types so Modelity could
    understand those, or to overwrite built-in type handlers.

    When this method is used then internal type cache is also cleared so it
    should be used at module level and before declaration of any Modelity
    models.

    :param typ:
        The type to register type handler for.

    :param factory:
        The type handler factory function to use for provided type.
    """
    from modelity._parsing.type_handler_factory import register_type_handler_factory

    return register_type_handler_factory(typ, factory)


@export
def create_type_handler(typ: Any, /, **type_opts):
    """Create type handler for provided type.

    This method is using cache internally so it returns same handler if called
    again with same type.

    :param typ:
        The type to create or get handler for.

    :param `**type_opts`:
        The optional type options to use.
    """
    from modelity._parsing.type_handler_factory import create_type_handler

    return create_type_handler(typ, **type_opts)


def _run_field_preprocessors(cls: type[Model], errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
    for hook in _int_hooks.collect_field_hooks(cls, "field_preprocessor", loc[-1]):  # type: ignore
        value = hook(cls, errors, loc, value)
        if value is Unset:
            return Unset
    return value


def _run_field_postprocessors(
    cls: type[Model], self: Model, errors: list[Error], loc: Loc, value: Any
) -> Union[Any, UnsetType]:
    for hook in _int_hooks.collect_field_hooks(cls, "field_postprocessor", loc[-1]):  # type: ignore
        value = hook(cls, self, errors, loc, value)
        if value is Unset:
            return Unset
    return value


def _collect_hooks_from_mixin_class(cls: type) -> Iterator[_int_hooks.IBaseHook]:
    for name in dir(cls):
        value = getattr(cls, name)
        if _int_hooks.is_base_hook(value):
            yield value
