import copy
import dataclasses
import functools
from typing import Any, Callable, Mapping, Optional, Sequence, Union, TypeVar, cast, get_args, get_origin
import typing_extensions

from modelity import _utils
from modelity.error import Error
from modelity.exc import ParsingError
from modelity.interface import (
    IFieldPostprocessingHook,
    IFieldPreprocessingHook,
    IModel,
    IModelHook,
    IModelVisitor,
    ITypeDescriptor,
)
from modelity.loc import Loc

from modelity.unset import Unset, UnsetType
from modelity.decorators import (
    #FieldPostprocessingHook,
    #FieldPreprocessingHook,
    field_preprocessor,
    field_postprocessor,
    _is_model_hook,
    _get_field_preprocessors,
    _get_field_postprocessors,
    model_prevalidator,
    model_postvalidator,
    field_validator,
)

T = TypeVar("T")


def type_descriptor_factory(typ: Any):
    """Register type descriptor factory function for type *typ*.

    This decorator can be used to register non user-defined types (f.e. from
    3rd party libraries) that cannot be added to Modelity typing system via
    ``__modelity_type_descriptor__`` static function.

    Check :ref:`registering-3rd-party-types-label` for more details.

    .. note:: This decorator must be used before first model is created or
              otherwise registered type might not be visible.

    .. versionadded:: 0.14.0

    :param typ:
        The type to register descriptor factory for.
    """
    from modelity._type_descriptors.all import registry

    def decorator(func):
        return registry.register_type_descriptor_factory(typ, func)

    return decorator


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
class BoundField:
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

    #: Dict containing all fields declared for a model.
    #:
    #: The name of a field is used as a key, while :class:`BoundField` class
    #: instance is used as a value.
    __model_fields__: Mapping[str, BoundField]

    #: List of user-defined hooks.
    #:
    #: Hooks are registered using decorators defined in the
    #: :mod:`modelity.model` module. A hook registered in base class is also
    #: inherited by child class.
    __model_hooks__: Sequence[IModelHook]

    def __new__(tp, name: str, bases: tuple, attrs: dict):
        attrs["__model_fields__"] = fields = {}  # type: ignore
        attrs["__model_hooks__"] = hooks = list[IModelHook]()
        for base in bases:
            fields.update(getattr(base, "__model_fields__", {}))
            hooks.extend(getattr(base, "__model_hooks__", []))
        annotations = attrs.pop("__annotations__", {})
        for field_name, annotation in annotations.items():
            field_info = attrs.pop(field_name, Unset)
            if not isinstance(field_info, FieldInfo):
                field_info = FieldInfo(default=field_info)
            bound_field = BoundField(
                field_name, annotation, _make_type_descriptor(annotation, field_info.type_opts), field_info
            )
            fields[field_name] = bound_field
        for key in dict(attrs):
            attr_value = attrs[key]
            if _is_model_hook(attr_value):
                hooks.append(attr_value)
                del attrs[key]
        hooks.sort(key=lambda x: x.__modelity_hook_id__)
        attrs["__slots__"] = tuple(annotations) + tuple(attrs.get("__slots__", [])) + ("__loc__",)
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

    def __init__(self, **kwargs) -> None:
        self.__loc__ = Loc()
        errors: list[Error] = []
        fields = self.__model_fields__
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
        for hook in _get_field_preprocessors(cls, loc[-1]):
            value = hook(cls, errors, loc, value)  # type: ignore
            if value is Unset:
                return Unset
        return value

    def __apply_field_postprocessors(self, errors, loc, value):
        cls = self.__class__
        for hook in _get_field_postprocessors(cls, loc[-1]):
            value = hook(cls, self, errors, loc, value)  # type: ignore
            if value is Unset:
                return Unset
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        field = self.__model_fields__.get(name)
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


def has_fields_set(model: Model) -> bool:
    """Check if *model* has at least one field set.

    :param model:
        The model object.
    """
    return next(iter(model), None) is not None


MT = TypeVar("MT", bound=Model)


def load(model_type: type[MT], data: dict, ctx: Any = None) -> MT:
    """Parse and validate given data using provided model type.

    This is a helper function meant to be used to create models from data that
    is coming from an untrusted source, like API request etc.

    On success, this function returns new instance of the given *model_type*.

    On failure, this function raises either :exc:`modelity.exc.ParsingError`
    (if it failed at parsing stage), or :exc:`modelity.model.ValidationError`
    (if it failed at model validation stage).

    Here's an example:

    .. testcode::

        from modelity.model import Model, load

        class Example(Model):
            foo: int
            bar: int

    .. doctest::

        >>> untrusted_data = {"foo": "123", "bar": "456"}
        >>> example = load(Example, untrusted_data)
        >>> example
        Example(foo=123, bar=456)

    :param model_type:
        The model type to parse data with.

    :param data:
        The data to be parsed.

    :param ctx:
        User-defined validation context.

        Check :meth:`Model.validate` for more information.
    """
    obj = model_type(**data)
    validate(obj, ctx=ctx)
    return obj


def dump(
    model: Model,
    exclude_unset: bool = False,
    exclude_none: bool = False,
    exclude_if: Optional[Callable[[Loc, Any], bool]] = None,
) -> dict:
    """Serialize model to a JSON-compatible dict.

    This is a helper function that uses :meth:`Model.dump` method underneath,
    giving it filters created from most common filtering options.

    :param model:
        The model to serialize.

    :param exclude_unset:
        Exclude :obj:`modelity.unset.Unset` values from the resulting dict.

    :param exclude_none:
        Exclude ``None`` values from the resulting dict.

    :param exclude_if:
        Custom generic exclusion function.

        Suitable for more complex cases not covered by the boolean flags
        available. Will be called with 2 arguments: location and the value, and
        should return ``True`` to exclude value, or ``False`` to leave it.

        Here's an example:

        .. testcode::

            import typing

            from modelity.loc import Loc

            def exclude_from_foo_or_when_none(loc: Loc, value: typing.Any) -> bool:
                return loc[0] == "foo" or value is None
    """
    from . import helpers

    return helpers.dump(model, exclude_unset=exclude_unset, exclude_none=exclude_none, exclude_if=exclude_if)


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
    from modelity._type_descriptors.all import registry

    return registry.make_type_descriptor(typ, type_opts or {})
