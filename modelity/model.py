import copy
import dataclasses
import functools
from typing import (
    Any,
    Callable,
    ClassVar,
    Iterator,
    Mapping,
    Optional,
    Union,
    TypeVar,
    cast,
    get_args,
    get_origin,
)
import typing_extensions

from modelity._internal import hooks as _int_hooks, model as _int_model
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.interface import (
    IField,
    IModelVisitor,
    ITypeDescriptor,
)
from modelity.loc import Loc
from modelity.types import is_deferred, is_optional, is_unsettable
from modelity.unset import Unset, UnsetType
from modelity import _utils

__all__ = export = _utils.ExportList()  # type: ignore

T = TypeVar("T")

_IGNORED_FIELD_NAMES = {
    "__model_fields__",
}


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

    .. versionadded:: 0.16.0

    .. versionchanged:: 0.19.0

        Added *title*, *description* and *examples* parameters.
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
    """Class for attaching metadata to model fields."""

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

    #: See :attr:`modelity.interface.IField.name`.
    name: str

    #: See :attr:`modelity.interface.IField.annotation`.
    typ: Any

    #: See :attr:`modelity.interface.IField.descriptor`.
    descriptor: ITypeDescriptor

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
    __model_fields__: Mapping[str, IField]

    def __new__(tp, name: str, bases: tuple, attrs: dict):
        attrs["__model_fields__"] = fields = dict[str, Field]()
        attrs["_modelity_hooks"] = hooks = list[_int_hooks.IBaseHook]()
        for base in bases:
            fields.update(getattr(base, "__model_fields__", {}))
            modelity_hooks = getattr(base, "_modelity_hooks", None)
            if modelity_hooks is not None:
                hooks.extend(modelity_hooks)
            else:
                hooks.extend(_collect_hooks_from_mixin_class(base))
        annotations = attrs.pop("__annotations__", {})
        for field_name, annotation in annotations.items():
            if field_name in _IGNORED_FIELD_NAMES:
                continue
            field_info = attrs.pop(field_name, Unset)
            if not isinstance(field_info, FieldInfo):
                field_info = FieldInfo(default=field_info)
            optional = is_optional(annotation)
            bound_field = Field(
                field_name,
                annotation,
                _int_model.make_type_descriptor(annotation, field_info.type_opts),
                field_info,
                optional=optional,
                unsettable=is_unsettable(annotation) if optional else False,
                deferred=is_deferred(annotation) if not optional else False,
            )
            fields[field_name] = bound_field
        for key in dict(attrs):
            attr_value = attrs[key]
            if _int_hooks.is_base_hook(attr_value):
                hooks.append(attr_value)
                del attrs[key]
        hooks.sort(key=lambda x: x.__modelity_hook_id__)
        attrs["__slots__"] = tuple(fields) + tuple(attrs.get("__slots__", []))
        return super().__new__(tp, name, bases, attrs)


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
    __model_fields__: ClassVar[Mapping[str, IField]]

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
                value = self.__parse(field.descriptor, errors, name, value)
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
        self, type_descriptor: ITypeDescriptor, errors: list[Error], field_name: str, value: Any
    ) -> Union[Any, UnsetType]:
        loc = Loc(field_name)
        cls = self.__class__
        value = _run_field_preprocessors(cls, errors, loc, value)  # type: ignore
        if value is Unset:
            return value
        value = type_descriptor.parse(errors, loc, value)
        if value is Unset:
            return value
        value = _run_field_postprocessors(cls, self, errors, loc, value)  # type: ignore
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        field = self.__class__.__model_fields__.get(name)
        if field is None:
            return super().__setattr__(name, value)
        errors: list[Error] = []
        value = self.__parse(field.descriptor, errors, name, value)
        if errors:
            raise ParsingError(self.__class__, tuple(errors))
        super().__setattr__(name, value)

    def __delattr__(self, name):
        setattr(self, name, Unset)

    def accept(self, visitor: IModelVisitor, loc: Loc):
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
                        field.descriptor.accept(visitor, field_loc, value)
                    visitor.visit_model_field_end(field_loc, value, field)
            visitor.visit_model_end(loc, self)


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
