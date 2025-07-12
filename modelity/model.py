import copy
import dataclasses
import functools
import inspect
from typing import Any, Callable, Optional, Union, TypeVar, cast, get_args, get_origin
import typing_extensions

from modelity import _utils
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError, ValidationError
from modelity.interface import (
    DISCARD,
    IBaseHook,
    IDumpFilter,
    IFieldHook,
    IFieldPreprocessingHook,
    IFieldPostprocessingHook,
    IFieldValidationHook,
    IModel,
    IModelHook,
    IModelPostvalidationHook,
    IModelPrevalidationHook,
    IModelValidationHook,
    ITypeDescriptor,
)
from modelity.loc import Loc

from modelity.unset import Unset, UnsetType

T = TypeVar("T")


def _make_model_validation_hook(func: Callable, hook_name: str) -> IModelValidationHook:

    @functools.wraps(func)
    def proxy(cls: type[IModel], self: IModel, root: IModel, ctx: Any, errors: list[Error], loc: Loc):
        kw: dict[str, Any] = {}
        if "cls" in given_params:
            kw["cls"] = cls
        if "self" in given_params:
            kw["self"] = self
        if "root" in given_params:
            kw["root"] = root
        if "ctx" in given_params:
            kw["ctx"] = ctx
        if "errors" in given_params:
            kw["errors"] = errors
        if "loc" in given_params:
            kw["loc"] = loc
        try:
            func(**kw)
        except ValueError as e:
            errors.append(ErrorFactory.exception(loc, str(e), type(e)))

    sig = inspect.signature(func)
    given_params = tuple(sig.parameters)
    supported_params = ("cls", "self", "root", "ctx", "errors", "loc")
    if not _utils.is_subsequence(given_params, supported_params):
        raise TypeError(
            f"function {func.__name__!r} has incorrect signature: "
            f"{_utils.format_signature(given_params)} is not a subsequence of "
            f"{_utils.format_signature(supported_params)}"
        )
    hook = cast(IModelValidationHook, proxy)
    hook.__modelity_hook_id__ = _utils.next_unique_id()
    hook.__modelity_hook_name__ = hook_name
    return hook


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


def field_preprocessor(*field_names: str):
    """Decorate model's method as a field preprocessing hook.

    Field preprocessors allow to execute user-defined filtering (like white
    character stripping) before value is passed further to the type parser.

    Check :class:`modelity.interface.IFieldParsingHook` protocol for more
    details.

    Here's an example use:

    .. testcode::

        from modelity.model import Model, field_preprocessor

        class FieldPreprocessorExample(Model):
            foo: str

            @field_preprocessor("foo")
            def _strip_white_characters(value):
                if isinstance(value, str):
                    return value.strip()
                return value

    :param `*field_names`:
        List of field names this preprocessor will be called for.

        If not set, then it will be called for every field.
    """

    def decorator(func: Callable):

        @functools.wraps(func)
        def proxy(cls: type[IModel], errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
            kw: dict[str, Any] = {}
            if "cls" in given_params:
                kw["cls"] = cls
            if "errors" in given_params:
                kw["errors"] = errors
            if "loc" in given_params:
                kw["loc"] = loc
            if "value" in given_params:
                kw["value"] = value
            try:
                return func(**kw)
            except TypeError as e:
                errors.append(ErrorFactory.exception(loc, str(e), type(e)))
                return Unset

        sig = inspect.signature(func)
        given_params = tuple(sig.parameters)
        supported_params = ("cls", "errors", "loc", "value")
        if not _utils.is_subsequence(given_params, supported_params):
            raise TypeError(
                f"field processor {func.__name__!r} has incorrect signature: {_utils.format_signature(given_params)} is not a subsequence of {_utils.format_signature(supported_params)}"
            )
        hook = cast(IFieldPreprocessingHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_name__ = IFieldPreprocessingHook.__modelity_hook_name__
        hook.__modelity_hook_field_names__ = set(field_names)
        return hook

    return decorator


def field_postprocessor(*field_names: str):
    """Decorate model's method as field postprocessing hook.

    Field postprocessors are executed just after value parsing and only if the
    parsing was successful. Postprocessing is the last step of value processing
    and can be used to perform additional user-defined and field-specific
    validation. Value returned by postprocessor is used as input value for
    another postprocessor if there are many postprocessors defined for a single
    field. Value returned by last postprocessor becomes final field's value.

    Check :class:`modelity.interface.IFieldParsingHook` protocol for the list
    of supported arguments and their meaning.

    Here's an example use:

    .. testcode::

        from modelity.model import Model, field_postprocessor

        class FieldPostprocessorExample(Model):
            foo: str

            @field_postprocessor("foo")
            def _strip_white_characters(value):
                return value.strip()  # The 'value' is guaranteed to be str when this gets called

    :param `*field_names`:
        List of field names this postprocessor will be called for.

        If not set, then it will be called for every field.
    """

    def decorator(func):

        @functools.wraps(func)
        def proxy(cls: type[IModel], self: IModel, errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
            kw: dict[str, Any] = {}
            if "cls" in given_params:
                kw["cls"] = cls
            if "self" in given_params:
                kw["self"] = self
            if "errors" in given_params:
                kw["errors"] = errors
            if "loc" in given_params:
                kw["loc"] = loc
            if "value" in given_params:
                kw["value"] = value
            try:
                return func(**kw)
            except TypeError as e:
                errors.append(ErrorFactory.exception(loc, str(e), type(e)))
                return Unset

        sig = inspect.signature(func)
        given_params = tuple(sig.parameters)
        supported_params = ("cls", "self", "errors", "loc", "value")
        if not _utils.is_subsequence(given_params, supported_params):
            raise TypeError(
                f"field processor {func.__name__!r} has incorrect signature: {_utils.format_signature(given_params)} is not a subsequence of {_utils.format_signature(supported_params)}"
            )
        hook = cast(IFieldPostprocessingHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_name__ = IFieldPostprocessingHook.__modelity_hook_name__
        hook.__modelity_hook_field_names__ = set(field_names)
        return hook

    return decorator


def model_prevalidator():
    """Decorate model's method as a model prevalidator.

    Prevalidators run before any other validators (including built-in ones),
    during the initial stage of model validation.

    Check :class:`modelity.interface.IModelValidationHook` protocol for the
    list of supported arguments that can be used by the decorated method.
    """

    def decorator(func) -> IModelPrevalidationHook:
        return cast(IModelPrevalidationHook, _make_model_validation_hook(func, IModelPrevalidationHook.__modelity_hook_name__))

    return decorator


def model_postvalidator():
    """Decorate model's method as a model postvalidator.

    Postvalidators run after all other validators, during the final stage of
    model validation.

    Check :class:`modelity.interface.IModelValidationHook` protocol for the
    list of supported arguments that can be used by the decorated method.
    """

    def decorator(func) -> IModelPostvalidationHook:
        return cast(IModelPostvalidationHook, _make_model_validation_hook(func, IModelPostvalidationHook.__modelity_hook_name__))

    return decorator


def field_validator(*field_names: str):
    """Decorate model's method as a field validator.

    Unlike model pre- and postvalidators, operating in the model scope, field
    validators are only executed if the field has value assigned. And since the
    value must pass parsing step, field validators can safely assume that the
    value already has correct type.

    Check :class:`modelity.interface.IFieldValidationHook` protocol for the
    list of supported method arguments and their meaning.

    :param `*field_names`:
        Names of fields to run this validator for.

        Leave empty to run for all fields defined in the current model.
    """

    def decorator(func) -> IFieldValidationHook:

        @functools.wraps(func)
        def proxy(cls: type[IModel], self: IModel, root: IModel, ctx: Any, errors: list[Error], loc: Loc, value: Any):
            kw: dict[str, Any] = {}
            if "cls" in given_params:
                kw["cls"] = cls
            if "self" in given_params:
                kw["self"] = self
            if "root" in given_params:
                kw["root"] = root
            if "ctx" in given_params:
                kw["ctx"] = ctx
            if "errors" in given_params:
                kw["errors"] = errors
            if "loc" in given_params:
                kw["loc"] = loc
            if "value" in given_params:
                kw["value"] = value
            try:
                func(**kw)
            except ValueError as e:
                errors.append(ErrorFactory.exception(loc, str(e), type(e)))

        sig = inspect.signature(func)
        supported_params = ("cls", "self", "root", "ctx", "errors", "loc", "value")
        given_params = tuple(sig.parameters)
        if not _utils.is_subsequence(given_params, supported_params):
            raise TypeError(
                f"function {func.__name__!r} has incorrect signature: "
                f"{_utils.format_signature(given_params)} is not a subsequence of "
                f"{_utils.format_signature(supported_params)}"
            )
        hook = cast(IFieldValidationHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_name__ = "field_validator"
        hook.__modelity_hook_field_names__ = set(field_names)
        return hook

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
    __model_fields__: dict[str, BoundField]

    #: List of user-defined hooks.
    #:
    #: Hooks are registered using decorators defined in the
    #: :mod:`modelity.model` module. A hook registered in base class is also
    #: inherited by child class.
    __model_hooks__: list[IBaseHook]

    def __new__(tp, name: str, bases: tuple, attrs: dict):

        def sort_hooks(target_list: list[IBaseHook]):
            target_list.sort(key=lambda x: x.__modelity_hook_id__)

        attrs["__model_fields__"] = fields = {}  # type: ignore
        attrs["__model_hooks__"] = hooks = []  # type: ignore
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
            hook_name = getattr(attr_value, "__modelity_hook_name__", None)
            if hook_name is not None and callable(attr_value):
                hooks.append(attr_value)
                del attrs[key]
        sort_hooks(hooks)
        attrs["__slots__"] = tuple(annotations) + tuple(attrs.get("__slots__", []))
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
        kv = (f"{k}={getattr(self, k)!r}" for k in self.__class__.__model_fields__)
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
        loc = Loc(name)
        value = self.__apply_field_preprocessors(errors, loc, value)
        if value is Unset:
            return super().__setattr__(name, value)
        value = type_descriptor.parse(errors, loc, value)
        value = self.__apply_field_postprocessors(errors, loc, value)
        return super().__setattr__(name, value)

    @classmethod
    def __apply_field_preprocessors(cls, errors, loc, value):
        for hook in _get_field_preprocessing_hooks(cls, loc[-1]):
            value = hook(cls, errors, loc, value)  # type: ignore
            if value is Unset:
                return Unset
        return value

    def __apply_field_postprocessors(self, errors, loc, value):
        cls = self.__class__
        for hook in _get_field_postprocessing_hooks(cls, loc[-1]):
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

    def dump(self, loc: Loc, filter: IDumpFilter) -> dict:
        """Dump model to a JSON-serializable dict.

        Check :class:`modelity.interface.IModel.dump` method for more details.
        """
        out = {}
        for name, field in self.__class__.__model_fields__.items():
            field_loc = loc + Loc(name)
            field_value = filter(field_loc, getattr(self, name))
            if field_value is not DISCARD:
                if field_value is Unset:
                    out[name] = field_value
                else:
                    dump_value = field.descriptor.dump(field_loc, field_value, filter)
                    if dump_value is not DISCARD:
                        out[name] = dump_value
        return out

    def validate(self, root: "Model", ctx: Any, errors: list[Error], loc: Loc):
        """Validate this model.

        Check :class:`modelity.interface.IModel.validate` method for more details.
        """
        cls = self.__class__
        for model_prevalidator in _get_model_prevalidation_hooks(cls):
            model_prevalidator(cls, self, root, ctx, errors, loc)  # type: ignore
        for name, field in cls.__model_fields__.items():
            value_loc = loc + Loc(name)
            value = getattr(self, name)
            if value is not Unset:
                for field_validator in _get_field_validation_hooks(cls, name):
                    field_validator(cls, self, root, ctx, errors, value_loc, value)  # type: ignore
                field.descriptor.validate(root, ctx, errors, value_loc, value)  # type: ignore
            elif not field.optional:
                errors.append(ErrorFactory.required_missing(value_loc))
        for model_postvalidator in _get_model_postvalidation_hooks(cls):
            model_postvalidator(cls, self, root, ctx, errors, loc)  # type: ignore


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

    def apply_filters(loc, value):
        for f in filters:
            value = f(loc, value)
            if value is DISCARD:
                return value
        return value

    filters = []
    if exclude_unset:
        filters.append(lambda l, v: DISCARD if v is Unset else v)
    if exclude_none:
        filters.append(lambda l, v: DISCARD if v is None else v)
    if exclude_if:
        filters.append(lambda l, v: DISCARD if exclude_if(l, v) else v)
    return model.dump(Loc(), apply_filters)


def validate(model: Model, ctx: Any = None):
    """Validate given model and raise :exc:`modelity.exc.ValidationError` if the
    model is invalid.

    :param model:
        The model to validate.

    :param ctx:
        User-defined context object.

        Check :meth:`Model.validate` for more information.
    """
    errors: list[Error] = []
    model.validate(model, ctx, errors, Loc())
    if errors:
        raise ValidationError(model, tuple(errors))


@functools.lru_cache
def _get_model_hooks_by_name(model_class: type[Model], hook_name: str) -> list[IModelHook]:
    result = []
    for hook in model_class.__model_hooks__:
        if hook.__modelity_hook_name__ == hook_name:
            result.append(hook)
    return cast(list[IModelHook], result)


@functools.lru_cache
def _get_field_hooks_by_name(model_class: type[Model], hook_name: str, field_name: str) -> list[IFieldHook]:
    result = []
    for hook in model_class.__model_hooks__:
        if hook.__modelity_hook_name__ == hook_name:
            hook = cast(IFieldHook, hook)
            field_names = hook.__modelity_hook_field_names__
            if len(field_names) == 0 or field_name in field_names:
                result.append(hook)
    return cast(list[IFieldHook], result)


def _get_model_prevalidation_hooks(model_class: type[Model]) -> list[IModelPrevalidationHook]:
    return cast(
        list[IModelPrevalidationHook],
        _get_model_hooks_by_name(model_class, IModelPrevalidationHook.__modelity_hook_name__),
    )


def _get_model_postvalidation_hooks(model_class: type[Model]) -> list[IModelPostvalidationHook]:
    return cast(
        list[IModelPostvalidationHook],
        _get_model_hooks_by_name(model_class, IModelPostvalidationHook.__modelity_hook_name__),
    )


def _get_field_validation_hooks(model_class: type[Model], field_name: str) -> list[IFieldValidationHook]:
    return cast(
        list[IFieldValidationHook],
        _get_field_hooks_by_name(model_class, IFieldValidationHook.__modelity_hook_name__, field_name),
    )


def _get_field_preprocessing_hooks(model_class: type[Model], field_name: str) -> list[IFieldPreprocessingHook]:
    return cast(
        list[IFieldPreprocessingHook],
        _get_field_hooks_by_name(model_class, IFieldPreprocessingHook.__modelity_hook_name__, field_name),
    )


def _get_field_postprocessing_hooks(model_class: type[Model], field_name: str) -> list[IFieldPostprocessingHook]:
    return cast(
        list[IFieldPostprocessingHook],
        _get_field_hooks_by_name(model_class, IFieldPostprocessingHook.__modelity_hook_name__, field_name),
    )


def _make_type_descriptor(typ: type[T], type_opts: Optional[dict] = None) -> ITypeDescriptor[T]:
    from modelity._type_descriptors.all import registry

    return registry.make_type_descriptor(typ, type_opts or {})
