import copy
import dataclasses
import functools
from typing import Any, Callable, Mapping, Optional, Sequence, Union, TypeVar, cast, get_args, get_origin
import typing_extensions

from modelity._internal import utils as _utils, hooks as _int_hooks
from modelity.error import Error
from modelity.exc import ParsingError
from modelity.interface import (
    IField,
    IModelHook,
    IModelVisitor,
    ITypeDescriptor,
)
from modelity.loc import Loc

from modelity.unset import Unset, UnsetType
from modelity.hooks import (
    #FieldPostprocessingHook,
    #FieldPreprocessingHook,
    field_preprocessor,
    field_postprocessor,
    #_is_model_hook,
    model_prevalidator,
    model_postvalidator,
    field_validator,
)

T = TypeVar("T")

_IGNORED_FIELD_NAMES = {"__model_fields__", "__model_hooks__"}


def field_info(
    *,
    default: Union[T, UnsetType] = Unset,
    default_factory: Union[Callable[[], T], UnsetType] = Unset,
    **type_opts,
) -> T:
    """Helper for creating :class:`FieldInfo` objects in a way that will
    satisfy code linters.

    .. versionadded:: 0.16.0
    """
    return cast(T, FieldInfo(default=default, default_factory=default_factory, type_opts=type_opts))


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

    #: Additional options for type descriptors.
    #:
    #: This can be used to pass additional type-specific settings, like
    #: input/output formats and more. The actual use of these options depends
    #: on the field type.
    type_opts: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Field:
    """Field created from annotation."""

    #: Field's name.
    name: str

    #: Field's type annotation.
    typ: Any

    #: Field's type descriptor object.
    descriptor: ITypeDescriptor

    #: Field's user-defined info object.
    field_info: Optional[FieldInfo] = None

    @functools.cached_property
    def optional(self) -> bool:
        """Flag telling if the field is optional.

        A field is optional if at least one of following criteria is met:

        * it is annotated with :class:`typing.Optional` type annotation,
        * it is annotated with :class:`modelity.types.StrictOptional` type annotation,
        * it is annotated with :class:`typing.Union` that allows ``None`` or ``Unset`` as one of valid values,
        * it has default value assigned.
        """
        if self.has_default():
            return True
        origin = get_origin(self.typ)
        args = get_args(self.typ)
        return origin is Union and (type(None) in args or UnsetType in args)

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

    #: Sequence of user-defined hooks.
    #:
    #: Hooks are registered using decorators defined in the
    #: :mod:`modelity.hooks` module. A hook registered in a base class is also
    #: inherited by a child class. The order of this sequence reflects hook
    #: declaration order.
    __model_hooks__: Sequence[IModelHook]

    def __new__(tp, name: str, bases: tuple, attrs: dict):
        attrs["__model_fields__"] = fields = dict[str, Field]()
        attrs["__model_hooks__"] = hooks = list[IModelHook]()
        for base in bases:
            fields.update(getattr(base, "__model_fields__", {}))
            hooks.extend(getattr(base, "__model_hooks__", []))
        annotations = attrs.pop("__annotations__", {})
        for field_name, annotation in annotations.items():
            if field_name in _IGNORED_FIELD_NAMES:
                continue
            field_info = attrs.pop(field_name, Unset)
            if not isinstance(field_info, FieldInfo):
                field_info = FieldInfo(default=field_info)
            bound_field = Field(
                field_name, annotation, _make_type_descriptor(annotation, field_info.type_opts), field_info
            )
            fields[field_name] = bound_field
        for key in dict(attrs):
            attr_value = attrs[key]
            if _int_hooks.is_model_hook(attr_value):
                hooks.append(attr_value)
                del attrs[key]
        hooks.sort(key=lambda x: x.__modelity_hook_id__)
        attrs["__slots__"] = tuple(fields) + tuple(attrs.get("__slots__", [])) + ("__loc__",)
        return super().__new__(tp, name, bases, attrs)


@typing_extensions.dataclass_transform(kw_only_default=True)
class Model(metaclass=ModelMeta):
    """Base class for creating models.

    To create a model using Modelity, you have to import this class, inherit
    from it, and provide fields in similar way as you would using
    :mod:`dataclasses` module. Here's an example:

    .. testcode::

        import datetime

        from modelity.model import Model

        class Book(Model):
            title: str
            author: str
            publisher: str
            page_count: int
            date_published: datetime.date

    And now, the class can be instantiated in similar way as dataclass with a
    difference that all fields in Modelity models are implicitly optional to
    allow gradual initialization like in example below:

    .. doctest::

        >>> book = Book()  # This will not fail
        >>> book.title = "My First Book"
        >>> book.author = "John Doe"
        >>> book.publisher = "Dummy Publishing Ltd."
        >>> book.page_count = 200
        >>> book.date_published = "2024-07-31"  # Model initialization completed

    .. note::

        Keyword args are also supported, so the initialization from above is
        equal to this:

        .. doctest::

            >>> book_via_kw = Book(
            ...     title="My First Book",
            ...     author="John Doe",
            ...     publisher="Dummy Publishing Ltd.",
            ...     page_count=200,
            ...     date_published="2024-07-31"
            ... )
            >>> book == book_via_kw
            True

    Now, to validate the model, you have to use :func:`modelity.model.validate`
    helper:

    .. doctest::

        >>> from modelity.model import validate
        >>> validate(book)  # OK, as all required fields are set

    This class implicitly implements :class:`modelity.interface.IModel`
    protocol.

    Check :ref:`quickstart` or :ref:`guide` for more examples.
    """

    #: A per-instance view of :attr:`ModelMeta.__model_fields__` attribute.
    __model_fields__: Mapping[str, IField]

    #: A per-instance view of :attr:`ModelMeta.__model_hooks__` attribute
    __model_hooks__: Sequence[IModelHook]

    def __init__(self, **kwargs) -> None:
        self.__loc__ = Loc()
        errors: list[Error] = []
        fields = self.__class__.__model_fields__
        for name, field in fields.items():
            value = kwargs.pop(name, Unset)
            if value is Unset:
                value = field.compute_default()
            if value is not Unset:
                self.__set_value(field.descriptor, errors, name, value)
            else:
                super().__setattr__(name, value)
        if errors:
            raise ParsingError(self.__class__, tuple(errors))

    def __repr__(self):
        kv = (f"{k}={getattr(self, k)!r}" for k in self.__model_fields__)
        return f"{self.__class__.__qualname__}({', '.join(kv)})"

    def __eq__(self, value):
        if self.__class__ is not value.__class__:
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

    def __set_value(self, type_descriptor: ITypeDescriptor, errors: list[Error], name: str, value: Any):
        if value is Unset:
            return super().__setattr__(name, value)
        loc = self.__loc__ + Loc(name)
        value = self.__apply_field_preprocessors(errors, loc, value)
        if value is Unset:
            return super().__setattr__(name, value)
        value = type_descriptor.parse(errors, loc, value)
        value = self.__apply_field_postprocessors(errors, loc, value)
        return super().__setattr__(name, value)

    @classmethod
    def __apply_field_preprocessors(cls, errors, loc, value):
        for hook in _int_hooks.get_field_preprocessors(cls, loc[-1]):
            value = hook(cls, errors, loc, value)  # type: ignore
            if value is Unset:
                return Unset
        return value

    def __apply_field_postprocessors(self, errors, loc, value):
        cls = self.__class__
        for hook in _int_hooks.get_field_postprocessors(cls, loc[-1]):
            value = hook(cls, self, errors, loc, value)  # type: ignore
            if value is Unset:
                return Unset
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        field = self.__class__.__model_fields__.get(name)
        if field is None:
            return super().__setattr__(name, value)
        errors: list[Error] = []
        self.__set_value(field.descriptor, errors, name, value)
        if errors:
            raise ParsingError(self.__class__, tuple(errors))

    def __delattr__(self, name):
        setattr(self, name, Unset)

    def accept(self, visitor: IModelVisitor):
        visitor.visit_model_begin(self.__loc__, self)
        for name, field in self.__class__.__model_fields__.items():
            loc = self.__loc__ + Loc(name)
            value = getattr(self, name)
            if value is Unset:
                visitor.visit_unset(loc, value)
            else:
                field.descriptor.accept(visitor, loc, value)
        visitor.visit_model_end(self.__loc__, self)


def validate(model: Model, ctx: Any = None):
    """Validate given model and raise :exc:`modelity.exc.ValidationError` if the
    model is invalid.

    :param model:
        The model to validate.

    :param ctx:
        User-defined context object.

        Check :meth:`Model.validate` for more information.
    """
    from . import helpers

    return helpers.validate(model, ctx)


def _make_type_descriptor(typ: type[T], type_opts: Optional[dict] = None) -> ITypeDescriptor[T]:
    from modelity._internal.type_descriptors.all import registry

    return registry.make_type_descriptor(typ, type_opts or {})
