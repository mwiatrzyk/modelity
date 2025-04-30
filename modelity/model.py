import copy
import dataclasses
import functools
import inspect
from typing import Any, Callable, Mapping, Optional, Sequence, Union, TypeVar, cast, get_args, get_origin
import typing_extensions

from modelity import _utils
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError, ValidationError
from modelity.interface import (
    DISCARD,
    IDumpFilter,
    IFieldParsingHook,
    IFieldValidationHook,
    IModel,
    IModelValidationHook,
    ITypeDescriptor,
)
from modelity.loc import Loc
from modelity._type_descriptors.main import make_type_descriptor as _make_type_descriptor
from modelity.unset import Unset, UnsetType

T = TypeVar("T")


def _make_field_parsing_hook(func: Callable) -> IFieldParsingHook:

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
    proxy.__creation_order__ = _utils.next_unique_id()  # type: ignore
    return proxy


def _make_model_validator(func) -> IModelValidationHook:

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
    proxy.__creation_order__ = _utils.next_unique_id()  # type: ignore
    return proxy


def make_type_descriptor(typ: type[T], **opts) -> ITypeDescriptor[T]:
    """Make type descriptor for provided type.

    Can be used to create descriptor for any type supported by Modelity
    library, plus user-defined types if necessary hook is provided in
    user-defined type.

    :param typ:
        The type to create descriptor for.

    :param `**opts`:
        Additional type-specific options for refining type parsers.

        Please proceed to :ref:`supported-types` for more details.
    """
    return _make_type_descriptor(typ, **opts)


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
        proxy = _make_field_parsing_hook(func)
        proxy.__model_field_preprocessor__ = field_names  # type: ignore
        return proxy

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

    def decorator(func: Callable):
        proxy = _make_field_parsing_hook(func)
        proxy.__model_field_postprocessor__ = field_names  # type: ignore
        return proxy

    return decorator


def model_prevalidator():
    """Decorate model's method as a model prevalidator.

    Prevalidators run before any other validators (including built-in ones),
    during the initial stage of model validation.

    Check :class:`modelity.interface.IModelValidationHook` protocol for the
    list of supported arguments that can be used by the decorated method.
    """

    def decorator(func) -> IModelValidationHook:
        proxy = _make_model_validator(func)
        proxy.__model_prevalidator__ = True  # type: ignore
        return proxy

    return decorator


def model_postvalidator():
    """Decorate model's method as a model postvalidator.

    Postvalidators run after all other validators, during the final stage of
    model validation.

    Check :class:`modelity.interface.IModelValidationHook` protocol for the
    list of supported arguments that can be used by the decorated method.
    """

    def decorator(func) -> IModelValidationHook:
        proxy = _make_model_validator(func)
        proxy.__model_postvalidator__ = True  # type: ignore
        return proxy

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
        proxy.__model_field_validator__ = field_names  # type: ignore
        proxy.__creation_order__ = _utils.next_unique_id()  # type: ignore
        return proxy

    return decorator


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
    default_factory: Callable[[], Any] = Unset  # type: ignore

    #: Mark the field as optional.
    #:
    #: Unlike :class:`typing.Optional`, which allows ``None`` as a valid value,
    #: this can be used to express more restricted optional that does not allow
    #: ``None``. This is useful for creating self-exclusive fields that cannot
    #: coexist in the model.
    optional: Optional[bool] = None

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

            * it is annotated with :class:`typing.Optional` type annotation
            * it is annotated with :class:`typing.Union` that allows ``None`` as a valid value
            * it is assigned with user-defined :class:`FieldInfo` object having
              :attr:`FieldInfo.optional` set to ``True``.
        """
        if self.field_info is not None and self.field_info.optional:
            return True
        origin = get_origin(self.typ)
        return origin is Union and type(None) in get_args(self.typ)

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
        else:
            return default_factory()


class ModelMeta(type):
    """Metaclass for models."""

    #: Dict of model fields.
    __model_fields__: dict[str, BoundField]

    #: List of user-defined model prevalidators.
    __model_prevalidators__: list[IModelValidationHook]

    #: List of user-defined model postvalidators.
    __model_postvalidators__: list[IModelValidationHook]

    #: Dict containing field validators.
    #:
    #: Each key is field name, and each value is ordered list of validators
    #: created for that field.
    __model_field_validators__: dict[str, list[IFieldValidationHook]]

    #: Dict of field preprocessors.
    #:
    #: Each key is a field name, and each value is an ordered list of parsing
    #: hooks to be called when the field is set and before field type parsing
    #: is performed.
    __model_field_preprocessors__: dict[str, list[IFieldParsingHook]]

    #: Dict of field postprocessors.
    __model_field_postprocessors__: dict[str, list[IFieldParsingHook]]

    def __new__(tp, name: str, bases: tuple, attrs: dict):

        def inherit_field_hooks(base: Any, target_dict: dict[str, list], hook_container_name: str):
            inherited_field_hooks = getattr(base, hook_container_name, {})
            if inherited_field_hooks:
                for name, hooks in inherited_field_hooks.items():
                    target_dict.setdefault(name, []).extend(hooks)

        def sort_hooks(target_list: list):
            target_list.sort(key=lambda x: x.__creation_order__)

        def sort_field_hooks(target_dict: dict[str, list]):
            for hooks in target_dict.values():
                sort_hooks(hooks)

        attrs["__model_fields__"] = fields = {}  # type: ignore
        attrs["__model_prevalidators__"] = prevalidators = []  # type: ignore
        attrs["__model_postvalidators__"] = postvalidators = []  # type: ignore
        attrs["__model_field_validators__"] = field_validators = {}  # type: ignore
        attrs["__model_field_preprocessors__"] = field_preprocessors = {}  # type: ignore
        attrs["__model_field_postprocessors__"] = field_postprocessors = {}  # type: ignore
        for base in bases:
            fields.update(getattr(base, "__model_fields__", {}))
            prevalidators.extend(getattr(base, "__model_prevalidators__", []))
            postvalidators.extend(getattr(base, "__model_postvalidators__", []))
            inherit_field_hooks(base, field_validators, "__model_field_validators__")
            inherit_field_hooks(base, field_preprocessors, "__model_field_preprocessors__")
            inherit_field_hooks(base, field_postprocessors, "__model_field_postprocessors__")
        annotations = attrs.pop("__annotations__", {})
        for field_name, annotation in annotations.items():
            field_info = attrs.pop(field_name, Unset)
            if not isinstance(field_info, FieldInfo):
                field_info = FieldInfo(default=field_info)
            bound_field = BoundField(
                field_name, annotation, make_type_descriptor(annotation, **field_info.type_opts), field_info
            )
            fields[field_name] = bound_field
        for key in dict(attrs):
            attr_value = attrs[key]
            if getattr(attr_value, "__model_prevalidator__", False) is True:
                prevalidators.append(attr_value)
                del attrs[key]
            elif getattr(attr_value, "__model_postvalidator__", False) is True:
                postvalidators.append(attr_value)
                del attrs[key]
            elif hasattr(attr_value, "__model_field_validator__"):
                field_names = attr_value.__model_field_validator__ or list(fields) or ["*"]
                for name in field_names:
                    target = field_validators.setdefault(name, [])
                    target.extend(field_validators.get("*", []))
                    target.append(attr_value)
                del attrs[key]
            elif hasattr(attr_value, "__model_field_preprocessor__"):
                field_names = attr_value.__model_field_preprocessor__ or list(fields) or ["*"]
                for name in field_names:
                    target = field_preprocessors.setdefault(name, [])
                    target.extend(field_preprocessors.get("*", []))
                    target.append(attr_value)
                del attrs[key]
            elif hasattr(attr_value, "__model_field_postprocessor__"):
                field_names = attr_value.__model_field_postprocessor__ or list(fields) or ["*"]
                for name in field_names:
                    target = field_postprocessors.setdefault(name, [])
                    target.extend(field_postprocessors.get("*", []))
                    target.append(attr_value)
                del attrs[key]
        sort_hooks(postvalidators)
        sort_field_hooks(field_validators)
        sort_field_hooks(field_preprocessors)
        attrs["__slots__"] = tuple(annotations) + tuple(attrs.get("__slots__", []))
        return super().__new__(tp, name, bases, attrs)


@typing_extensions.dataclass_transform(kw_only_default=True)
class Model(metaclass=ModelMeta):
    """Base class for creating models.

    This class implicitly implements :class:`modelity.interface.IModel`
    protocol.
    """

    __slots__ = ["__loc__"]

    def __init__(self, **kwargs) -> None:
        self.__loc__: Loc = Loc()
        errors: list[Error] = []
        for name, field in self.__class__.__model_fields__.items():
            value = kwargs.pop(name, Unset)
            if value is Unset:
                value = field.compute_default()
            self.__set_value(field.descriptor, errors, name, value)
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
        cls = self.__class__
        loc = Loc(name)
        for preprocessor in cls.__model_field_preprocessors__.get(name, []):
            value = preprocessor(cls, errors, loc, value)  # type: ignore
            if value is Unset:
                return super().__setattr__(name, value)
        value = type_descriptor.parse(errors, loc, value)
        value = self.__apply_field_parsing_hooks(cls.__model_field_postprocessors__.get(name, []), errors, loc, value)
        return super().__setattr__(name, value)

    @classmethod
    def __apply_field_parsing_hooks(
        cls, hook_list: list[IFieldParsingHook], errors: list[Error], loc: Loc, value: Any
    ) -> Union[Any, UnsetType]:
        for hook in hook_list:
            value = hook(cls, errors, loc, value)  # type: ignore
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        field = self.__class__.__model_fields__.get(name)
        if field is None:
            return super().__setattr__(name, value)
        errors: list[Error] = []
        self.__set_value(field.descriptor, errors, name, value)
        if errors:
            raise ParsingError(
                self.__class__, tuple(Error(self.__loc__ + x.loc, x.code, x.msg, x.value, x.data) for x in errors)
            )

    def __delattr__(self, name):
        setattr(self, name, Unset)

    def dump(self, filter: IDumpFilter) -> dict:
        """Serialize model to dict.

        :param loc:
            The location of this model if it is nested inside another model, or
            empty location otherwise.

        :param filter:
            The filter function.

            Check :class:`IDumpFilter` class for more details.
        """
        out = {}
        for name, field in self.__class__.__model_fields__.items():
            field_loc = self.__loc__ + Loc(name)
            field_value = filter(field_loc, getattr(self, name))
            if field_value is not DISCARD:
                if field_value is Unset:
                    out[name] = field_value
                else:
                    dump_value = field.descriptor.dump(field_loc, field_value, filter)
                    if dump_value is not DISCARD:
                        out[name] = dump_value
        return out

    def validate(self, root: "Model", ctx: Any, errors: list[Error]):
        """Validate this model.

        :param root:
            Reference to the root model.

            Root model is the model for which this method was initially called.
            This can be used by nested models to access entire model during
            validation.

        :param ctx:
            User-defined context object to be shared across all validators.

            It is completely transparent to Modelity, so any value can be used
            here, but recommended is ``None`` if no context is used.

        :param errors:
            List to populate with any errors found during validation.

            Should initially be empty.

        :param loc:
            The location of this model if it is nested inside another model, or
            empty location otherwise.
        """
        cls = self.__class__
        for model_prevalidator in cls.__model_prevalidators__:
            model_prevalidator(cls, self, root, ctx, errors, self.__loc__)  # type: ignore
        for name, field in cls.__model_fields__.items():
            loc = self.__loc__ + Loc(name)
            value = getattr(self, name)
            if value is not Unset:
                for field_validator in cls.__model_field_validators__.get(name, []):
                    field_validator(cls, self, root, ctx, errors, loc, value)  # type: ignore
                field.descriptor.validate(root, ctx, errors, loc, value)  # type: ignore
            elif not field.optional:
                errors.append(ErrorFactory.required_missing(loc))
        for model_postvalidator in cls.__model_postvalidators__:
            model_postvalidator(cls, self, root, ctx, errors, self.__loc__)  # type: ignore


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
    return model.dump(apply_filters)


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
    model.validate(model, ctx, errors)
    if errors:
        raise ValidationError(model, tuple(errors))
