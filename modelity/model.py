import dataclasses
import functools
import inspect
import io
from typing import Any, Callable, Mapping, Optional, Protocol, Sequence, Union, get_args, get_origin
import typing_extensions

from modelity import _utils
from modelity.error import Error, ErrorFactory
from modelity.exc import ModelParsingError, ParsingError, ValidationError
from modelity.interface import IDumpFilter, IModelValidatorCallable, ITypeDescriptor
from modelity.loc import Loc
from modelity.type_descriptors.main import make_type_descriptor
from modelity.unset import Unset, UnsetType


def model_validator(pre: bool = False):
    """Decorate custom function as a model-level validator.

    Decorated function can be defined without arguments, or with any
    subsequence of the following arguments (the order does matter):

    ``cls``
        Model class.

    ``self``
        Model object.

    ``root``
        Root model object.

        Root model is the object for which :func:`modelity.model.validate` was
        called and allows to access whole model for even more complex
        validation.

    ``errors``
        The mutable list of errors.

        The validator can add its errors into this list.

    ``loc``
        The location of the *self* model.

    :param pre:
        Run this validator before any other validators.
    """

    def decorator(func):

        @functools.wraps(func)
        def proxy(cls: type["Model"], self: "Model", root: "Model", ctx: Any, errors: list[Error], loc: Loc):
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
            except (ValueError, TypeError) as e:
                errors.append(ErrorFactory.exception(loc, str(e), type(e)))

        sig = inspect.signature(func)
        given_params = tuple(sig.parameters)
        supported_params = ("cls", "self", "root", "ctx", "errors", "loc")
        if not _utils.is_subsequence(given_params, supported_params):
            raise TypeError(
                f"function {func.__name__!r} has incorrect signature: {_utils.format_signature(given_params)} is not a subsequence of {_utils.format_signature(supported_params)}"
            )
        if pre:
            proxy.__model_prevalidator__ = True
        else:
            proxy.__model_postvalidator__ = True
        return proxy

    return decorator


@dataclasses.dataclass
class FieldInfo:
    """Class for attaching metadata to model fields."""

    #: Default field value.
    default: Any = Unset

    #: Mark the field as optional.
    #:
    #: Unlike :class:`typing.Optional`, which is more convenient in most cases,
    #: this kind of optional disallows ``None``.
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
    type: Any

    #: Field's type descriptor object.
    type_descriptor: ITypeDescriptor

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
        origin = get_origin(self.type)
        return origin is Union and type(None) in get_args(self.type)

    def compute_default(self) -> Union[Any, UnsetType]:
        """Compute default value for this field."""
        if self.field_info is None:
            return Unset
        if self.field_info.default is not Unset:
            return self.field_info.default
        return Unset


class ModelMeta(type):
    """Metaclass for models."""

    #: Dict containing model fields.
    __model_fields__: dict[str, BoundField]

    #: List with model postvalidators.
    __model_postvalidators__: list[IModelValidatorCallable]

    def __new__(tp, name: str, bases: tuple, attrs: dict):
        attrs["__model_fields__"] = fields = {}
        attrs["__model_postvalidators__"] = model_postvalidators = []
        for base in bases:
            fields.update(getattr(base, "__model_fields__", {}))
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
            if getattr(attr_value, "__model_postvalidator__", False) is True:
                model_postvalidators.append(attr_value)
                del attrs[key]
        attrs["__slots__"] = tuple(annotations)
        return super().__new__(tp, name, bases, attrs)


@typing_extensions.dataclass_transform(kw_only_default=True)
class Model(metaclass=ModelMeta):
    """Base class for data models."""

    def __init__(self, **kwargs):
        errors = []
        for name, field in self.__class__.__model_fields__.items():
            value = kwargs.pop(name, Unset)
            if value is Unset:
                value = field.compute_default()
            if value is not Unset:
                super().__setattr__(name, field.type_descriptor.parse(errors, Loc(name), value))
            else:
                super().__setattr__(name, value)
        if errors:
            raise ModelParsingError(self, tuple(errors))

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

    def dump(self, loc: Loc, filter: IDumpFilter) -> dict:
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
            field_loc = loc + Loc(name)
            field_value = filter(field_loc, getattr(self, name))
            if field_value is not IDumpFilter.SKIP:
                if field_value is Unset:
                    out[name] = field_value
                else:
                    dump_value = field.type_descriptor.dump(field_loc, field_value, filter)
                    if dump_value is not IDumpFilter.SKIP:
                        out[name] = dump_value
        return out

    def validate(self, root: "Model", ctx: Any, errors: list[Error], loc: Loc):
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
        for name, field in cls.__model_fields__.items():
            value = getattr(self, name)
            if value is not Unset:
                field.type_descriptor.validate(root, ctx, errors, loc + Loc(name), value)
            elif not field.optional:
                errors.append(ErrorFactory.required_missing(loc + Loc(name)))
        for validator in cls.__model_postvalidators__:
            validator(cls, self, root, ctx, errors, loc)


def dump(
    model: Model,
    exclude_unset: bool = False,
    exclude_none: bool = False,
    exclude_if: Optional[Callable[[Loc, Any], bool]] = None,
) -> dict:
    """Serialize model to a JSON-compatible dict.

    This is a helper function that uses :meth:`Model.dump` underneath,
    supplying it with most common filtering options.

    :param model:
        The model to serialize.

    :param exclude_unset:
        Exclude unset fields from the resulting dict.

    :param exclude_none:
        Exclude fields that are set to ``None`` from the resulting dict.

    :param exclude_if:
        Custom exclusion function.

        Will be called with ``(loc, value)`` arguments, where *loc* is a value
        location, and *value* is the value to be serialized. Can be used to to
        perform more advanced exclusion based on both location and a value.
        Should return ``True`` to exclude value, or ``False`` to retain it.
    """

    def apply_filters(loc, value):
        for f in filters:
            value = f(loc, value)
            if value is IDumpFilter.SKIP:
                return value
        return value

    filters = []
    if exclude_unset:
        filters.append(lambda l, v: IDumpFilter.SKIP if v is Unset else v)
    if exclude_none:
        filters.append(lambda l, v: IDumpFilter.SKIP if v is None else v)
    if exclude_if:
        filters.append(lambda l, v: IDumpFilter.SKIP if exclude_if(l, v) else v)
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
    errors = []
    model.validate(model, ctx, errors, Loc())
    if errors:
        raise ValidationError(model, tuple(errors))


# import enum
# import functools
# import inspect
# import itertools
# import dataclasses
# from typing import (
#     Any,
#     Callable,
#     Dict,
#     Iterator,
#     List,
#     Mapping,
#     Optional,
#     Sequence,
#     Set,
#     Tuple,
#     Type,
#     Union,
#     cast,
#     TypeVar,
# )
# from typing_extensions import dataclass_transform

# from modelity import _utils
# from modelity.error import ErrorCode, Error, ErrorFactory
# from modelity.exc import ParsingError, ValidationError
# from modelity.field import BoundField, Field
# from modelity.invalid import Invalid
# from modelity.loc import Loc
# from modelity.interface import IDumpFilter, IConfig, IConfig, IError, ITypeParserProvider
# from modelity.providers import CachingTypeParserProviderProxy
# from modelity._parsing.type_parsers.all import provider as _root_provider
# from modelity.unset import Unset
# from modelity.interface import IModel

# _reserved_names: Set[str] = set()
# _order_id = itertools.count()


# class _DecoratorInfo:
#     __slots__ = ("ordering_id",)

#     ordering_id: int

#     def __init__(self):
#         self.ordering_id = next(_order_id)


# class _ProcessorDecoratorInfo(_DecoratorInfo):
#     __slots__ = ("type", "field_names")

#     class Type(enum.Enum):
#         PRE = 1
#         POST = 2

#     type: Type
#     field_names: Tuple[str, ...]

#     def __init__(self, type: Type, field_names: Tuple[str, ...]):
#         super().__init__()
#         self.type = type
#         self.field_names = field_names


# class _FieldValidatorDecoratorInfo(_DecoratorInfo):
#     __slots__ = ("field_names",)

#     field_names: Tuple[str, ...]

#     def __init__(self, field_names: Tuple[str, ...]):
#         super().__init__()
#         self.field_names = field_names


# class _ModelValidatorDecoratorInfo(_DecoratorInfo):
#     __slots__ = ("pre",)

#     pre: bool

#     def __init__(self, pre: bool):
#         super().__init__()
#         self.pre = pre


# def _wrap_field_processor(func: Callable):

#     @functools.wraps(func)
#     def proxy(cls: Type["Model"], loc: Loc, name: str, value: Any, config: IConfig) -> Union[Any, Invalid]:
#         kw: Dict[str, Any] = {}
#         if "cls" in given_params:
#             kw["cls"] = cls
#         if "loc" in given_params:
#             kw["loc"] = loc
#         if "name" in given_params:
#             kw["name"] = name
#         if "value" in given_params:
#             kw["value"] = value
#         if "config" in given_params:
#             kw["config"] = config
#         try:
#             result = func(**kw)
#         except ValueError as e:
#             return Invalid(value, ErrorFactory.value_error(loc, str(e)))
#         except TypeError as e:
#             print(e)
#             return Invalid(value, ErrorFactory.type_error(loc, str(e)))
#         if isinstance(result, Invalid):
#             return Invalid(result.value, *(Error(loc + e.loc, e.code, e.msg, data=e.data) for e in result.errors))
#         return result

#     sig = inspect.signature(func)
#     given_params = tuple(sig.parameters)
#     supported_params = ("cls", "loc", "name", "value", "config")
#     if not _utils.is_subsequence(given_params, supported_params):
#         raise TypeError(
#             f"field processor {func.__name__!r} has incorrect signature: {_utils.format_signature(given_params)} is not a subsequence of {_utils.format_signature(supported_params)}"
#         )
#     return proxy


# def _dump_model(value: "Model", loc: Loc, func: IDumpFilter) -> Tuple[dict, bool]:
#     result = {}
#     for field_name in value.__class__.__fields__:
#         dump_value, skip = _dump_any(getattr(value, field_name), loc + Loc(field_name), func)
#         if not skip:
#             result[field_name] = dump_value
#     return result, False


# def _dump_any(value: Any, loc: Loc, func: IDumpFilter) -> Tuple[Any, bool]:
#     value, skip = func(value, loc)
#     if skip:
#         return value, skip
#     if isinstance(value, (str, bytes)):
#         return value, False
#     if isinstance(value, Model):
#         return _dump_model(value, loc, func)
#     if isinstance(value, Mapping):
#         return _dump_mapping(value, loc, func)
#     if isinstance(value, Sequence):
#         return _dump_sequence(value, loc, func)
#     return value, False


# def _dump_mapping(value: Mapping, loc: Loc, func: IDumpFilter) -> Tuple[dict, bool]:
#     result = {}
#     for key, value in value.items():
#         dump_value, skip = _dump_any(value, loc + Loc(key), func)
#         if not skip:
#             result[key] = dump_value
#     return result, False


# def _dump_sequence(value: Sequence, loc: Loc, func: IDumpFilter) -> Tuple[list, bool]:
#     result = []
#     for i, value in enumerate(value):
#         dump_value, skip = _dump_any(value, loc + Loc(i), func)
#         if not skip:
#             result.append(dump_value)
#     return result, False


# def _validate_model(obj: "Model", loc: Loc, errors: List[IError], root: "Model", config: IConfig):
#     cls = obj.__class__
#     for model_validator in cls._model_prevalidators:
#         errors.extend(model_validator(cls, obj, root, loc, errors, config))
#     for name, field_info in cls.__fields__.items():
#         field_loc = loc + Loc(name)
#         value = getattr(obj, name)
#         if value is Unset:
#             if field_info.is_required():
#                 errors.append(Error(field_loc, ErrorCode.REQUIRED_MISSING, "this field is required"))
#             continue
#         for constraint in field_info.constraints:
#             check_result = constraint(value, field_loc, config)
#             if isinstance(check_result, Invalid):
#                 errors.extend(check_result.errors)
#         _validate_any(value, field_loc, errors, root, config)
#         for field_validator in cls._field_validators.get(name, []):
#             errors.extend(field_validator(cls, obj, root, field_loc, name, value))
#     for model_validator in cls._model_postvalidators:
#         errors.extend(model_validator(cls, obj, root, loc, errors, config))


# def _validate_any(obj: Any, loc: Loc, errors: List[IError], root: "Model", config: IConfig):
#     if isinstance(obj, IModel):
#         _validate_model(cast(Model, obj), loc, errors, root, config)
#     elif isinstance(obj, Mapping):
#         for k, v in obj.items():
#             _validate_any(v, loc + Loc(k), errors, root, config)
#     elif isinstance(obj, Sequence) and type(obj) not in (str, bytes, bytearray):
#         for i, v in enumerate(obj):
#             _validate_any(v, loc + Loc(i), errors, root, config)


# def _get_model_field_value(obj: "Model", loc: Loc) -> Optional[Any]:
#     root, remainder = loc[0], loc[1:]
#     field_value = getattr(obj, root, Unset)
#     if field_value is Unset:
#         return None
#     if not remainder:
#         return field_value
#     return _get_any_value(field_value, remainder)


# def _get_mapping_value(obj: Mapping, loc: Loc) -> Optional[Any]:
#     root, remainder = loc[0], loc[1:]
#     value = obj.get(root, Unset)
#     if value is Unset:
#         return None
#     if not remainder:
#         return value
#     return _get_any_value(value, remainder)


# def _get_sequence_value(obj: Sequence, loc: Loc) -> Optional[Any]:
#     root, remainder = loc[0], loc[1:]
#     try:
#         value = obj[root]
#     except IndexError:
#         return None
#     if not remainder:
#         return value
#     return _get_any_value(value, remainder)


# def _get_any_value(obj: Any, loc: Loc) -> Optional[Any]:
#     if isinstance(obj, IModel):
#         return _get_model_field_value(cast(Model, obj), loc)
#     if isinstance(obj, Mapping):
#         return _get_mapping_value(obj, loc)
#     if isinstance(obj, Sequence):
#         return _get_sequence_value(obj, loc)
#     return None


# def field_validator(*field_names: str):
#     """Decorate custom function as a field validator.

#     Field validators are executed only if field has value assigned, implying
#     that the value has correct type (as it has to be successfully parsed
#     first).

#     Decorated function can use any combination (including empty one) of these
#     arguments:

#     ``cls``
#         Model class.

#     ``self``
#         Model instance.

#     ``root``
#         Root model instance.

#         This is the model for which :meth:`Model.validate` was called.

#     ``loc``
#         Field's location inside a model.

#     ``name``
#         Name of the field being validated.

#     ``value``
#         Value of the field being validated.

#     .. note:: The order must be preserved if multiple arguments are used.

#     :param `*field_names`:
#         Names of fields to run this validator for.

#         If none given, then it will run for all fields in a model it is declared in.
#     """

#     def decorator(func):

#         @functools.wraps(func)
#         def proxy(cls: Type["Model"], self: "Model", root: "Model", loc: Loc, name: str, value: Any):
#             kw: Dict[str, Any] = {}
#             if "cls" in given_params:
#                 kw["cls"] = cls
#             if "self" in given_params:
#                 kw["self"] = self
#             if "root" in given_params:
#                 kw["root"] = root
#             if "loc" in given_params:
#                 kw["loc"] = loc
#             if "name" in given_params:
#                 kw["name"] = name
#             if "value" in given_params:
#                 kw["value"] = value
#             try:
#                 result = func(**kw)
#             except ValueError as e:
#                 return (Error(loc, ErrorCode.VALUE_ERROR, msg=str(e)),)  # TODO: config.create_error
#             except TypeError as e:
#                 return (Error(loc, ErrorCode.TYPE_ERROR, msg=str(e)),)
#             if result is None:
#                 return tuple()
#             if isinstance(result, Error):
#                 return (result,)
#             return tuple(result)

#         sig = inspect.signature(func)
#         supported_params = ("cls", "self", "root", "loc", "name", "value")
#         given_params = tuple(sig.parameters)
#         if not _utils.is_subsequence(given_params, supported_params):
#             raise TypeError(
#                 f"incorrect field validator's signature; {_utils.format_signature(given_params)} is not a subsequence of {_utils.format_signature(supported_params)}"
#             )
#         proxy.__modelity_decorator_info__ = _FieldValidatorDecoratorInfo(field_names)
#         return proxy

#     return decorator


# def model_validator(pre: bool = False):
#     """Decorate custom function as a model validator.

#     Unlike field validators, model validators are always executed, either
#     before or after other validators (depending on the *pre* flag value).

#     Decorated function can use any combination (including empty one) of these
#     arguments:

#     ``cls``
#         Model class.

#     ``self``
#         Model instance.

#     ``root``
#         Root model instance.

#         This is the model for which :meth:`Model.validate` was called.

#     ``loc``
#         The absolute location of the model being validated.

#     ``errors``
#         List of errors.

#         Can be manipulated by validator.

#     .. note:: The order must be preserved if multiple arguments are used.

#     :param pre:
#         Run this validator before any other validators.
#     """

#     def decorator(func):

#         @functools.wraps(func)
#         def proxy(cls: Type["Model"], self: "Model", root: "Model", loc: Loc, errors: List[Error], config: IConfig):
#             kw: Dict[str, Any] = {}
#             if "cls" in given_params:
#                 kw["cls"] = cls
#             if "self" in given_params:
#                 kw["self"] = self
#             if "root" in given_params:
#                 kw["root"] = root
#             if "loc" in given_params:
#                 kw["loc"] = loc
#             if "errors" in given_params:
#                 kw["errors"] = errors
#             if "config" in given_params:
#                 kw["config"] = config
#             try:
#                 result = func(**kw)
#             except ValueError as e:
#                 return (Error(loc, ErrorCode.VALUE_ERROR, msg=str(e)),)  # TODO: config.create_error
#             except TypeError as e:
#                 return (Error(loc, ErrorCode.TYPE_ERROR, msg=str(e)),)
#             if result is None:
#                 return tuple()
#             if isinstance(result, Error):
#                 return (result,)
#             return tuple(result)

#         sig = inspect.signature(func)
#         given_params = tuple(sig.parameters)
#         supported_params = ("cls", "self", "root", "loc", "errors", "config")
#         if not _utils.is_subsequence(given_params, supported_params):
#             raise TypeError(
#                 f"model validator {func.__name__!r} has incorrect signature: {_utils.format_signature(given_params)} is not a subsequence of {_utils.format_signature(supported_params)}"
#             )
#         proxy.__modelity_decorator_info__ = _ModelValidatorDecoratorInfo(pre)
#         return proxy

#     return decorator


# def preprocessor(*field_names: str):
#     """Decorate a function as a field value preprocessor.

#     Preprocessors are called when value is set, before type parsing takes
#     place. The role of preprocessors is to perform input data filtering for
#     further steps like type parsing and postprocessors.

#     Decorated function can use any combination of the arguments from the list
#     below:

#     ``cls``
#         Model type.

#     ``loc``
#         Field's location inside model tree.

#     ``name``
#         Field's name.

#     ``value``
#         Field's candidate value.

#     .. note:: The order must be preserved if multiple arguments are used.

#     :param `*field_names`:
#         List of field names this preprocessor will be called for.

#         If not set, then it will be called for every field.
#     """

#     def decorator(func: Callable):
#         proxy = _wrap_field_processor(func)
#         proxy.__modelity_decorator_info__ = _ProcessorDecoratorInfo(_ProcessorDecoratorInfo.Type.PRE, field_names)
#         return proxy

#     return decorator


# def postprocessor(*field_names: str):
#     """Decorate a function as a field value postprocessor.

#     Postprocessors are called after preprocessors and type parsing, therefore
#     it can be assumed that a value is of valid type when postprocessors are
#     called. Postprocessors can be used to perform field-specific additional
#     processing, or to run field-specific validation that should fail on data
#     parsing step.

#     Decorated function can use any combination of the arguments from the list
#     below:

#     ``cls``
#         Model type.

#     ``loc``
#         Field's location inside model tree.

#     ``name``
#         Field's name.

#     ``value``
#         Field's parsed value.

#     .. note:: The order must be preserved if multiple arguments are used.

#     :param `*field_names`:
#         List of field names this postprocessor will be called for.

#         If left empty, then it will be called for every field.
#     """

#     def decorator(func: Callable):
#         proxy = _wrap_field_processor(func)
#         proxy.__modelity_decorator_info__ = _ProcessorDecoratorInfo(_ProcessorDecoratorInfo.Type.POST, field_names)
#         return proxy

#     return decorator


# def field(default: Any = Unset, optional: bool = False) -> "Field":
#     """Helper used to declare additional metadata for model field.

#     :param default:
#         Field's default value.

#     :param optional:
#         Flag telling that the field is optional.

#         This can be used to declare fields that can either be set to given type
#         or not set at all, as opposed to :class:`typing.Optional`, which is
#         defacto an union of type ``T`` and ``NoneType``.
#     """
#     return Field(default=default, optional=optional)


# def get_builtin_type_parser_provider() -> ITypeParserProvider:
#     """Get instance of :class:`ITypeParserProvider` class containing all built-in
#     type parsers.

#     This can be used to add custom types simply by creating custom type parser
#     provider and attaching this one to add built-in types.
#     """
#     return _root_provider


# @dataclasses.dataclass()
# class Config:
#     """Model configuration object.

#     Custom instances of this class, or subclass of this class, can be set via
#     :attr:`Model.__config__` attribute to customize behavior of the model. For
#     example, it will be necessary to explicitly configure model to register
#     custom type parser factories.

#     When creating custom config instances it is recommended to additionally
#     create custom base class for models that will use provided configuration.
#     """

#     #: Provider used to find type parser.
#     #:
#     #: Can be customized to allow user-defined type to be used by the library.
#     type_parser_provider: ITypeParserProvider = dataclasses.field(
#         default_factory=lambda: CachingTypeParserProviderProxy(get_builtin_type_parser_provider())
#     )

#     #: Placeholder for user-defined data.
#     user_data: Optional[dict] = None


# class ModelMeta(type):
#     """Metaclass for :class:`Model` class."""

#     __config__: IConfig
#     __fields__: Mapping[str, BoundField]
#     _preprocessors: Mapping[str, Sequence[Callable]]
#     _postprocessors: Mapping[str, Sequence[Callable]]
#     _field_validators: Mapping[str, Sequence[Callable]]
#     _model_prevalidators: Sequence[Callable]
#     _model_postvalidators: Sequence[Callable]

#     def __new__(tp, classname: str, bases: Tuple[Type], attrs: dict):

#         def inherit_fields():
#             for b in bases:
#                 yield from getattr(b, "__fields__", {}).items()

#         def inherit_mixed_in_annotations():
#             for b in filter(lambda b: not isinstance(b, ModelMeta), bases):
#                 yield from getattr(b, "__annotations__", {}).items()

#         def inherit_decorators():
#             for b in bases:
#                 for attr_name in dir(b):
#                     attr_value = getattr(b, attr_name)
#                     if callable(attr_value) and hasattr(attr_value, "__modelity_decorator_info__"):
#                         yield attr_value

#         def iter_decorators() -> Iterator[Tuple[Callable, _DecoratorInfo]]:
#             for obj in itertools.chain(inherit_decorators(), attrs.values()):
#                 if callable(obj):
#                     decorator_info = getattr(obj, "__modelity_decorator_info__", None)
#                     if decorator_info is not None:
#                         yield obj, decorator_info

#         fields = dict(inherit_fields())
#         for field_name, type in itertools.chain(
#             inherit_mixed_in_annotations(), attrs.get("__annotations__", {}).items()
#         ):
#             if field_name in _reserved_names:
#                 raise TypeError(f"the name {field_name!r} is reserved by Modelity and cannot be used as field name")
#             field_info = attrs.pop(field_name, None)
#             if field_info is None:
#                 field_info = BoundField(field_name, type)
#             elif isinstance(field_info, Field):
#                 field_info = BoundField(
#                     field_name,
#                     type,
#                     default=field_info.default,
#                     optional=field_info.optional,
#                 )
#             else:
#                 field_info = BoundField(field_name, type, default=field_info)
#             fields[field_name] = field_info
#         preprocessors: Dict[str, List[Callable]] = {}
#         postprocessors: Dict[str, List[Callable]] = {}
#         model_prevalidators: List[Callable] = []
#         model_postvalidators: List[Callable] = []
#         field_validators: Dict[str, List[Callable]] = {}
#         for func, decorator_info in sorted(iter_decorators(), key=lambda x: x[1].ordering_id):
#             if isinstance(decorator_info, _ProcessorDecoratorInfo):
#                 target_map = (
#                     preprocessors if decorator_info.type == _ProcessorDecoratorInfo.Type.PRE else postprocessors
#                 )
#                 for field_name in decorator_info.field_names or fields:
#                     target_map.setdefault(field_name, []).append(func)
#             elif isinstance(decorator_info, _FieldValidatorDecoratorInfo):
#                 for field_name in decorator_info.field_names or fields:
#                     field_validators.setdefault(field_name, []).append(func)
#             elif isinstance(decorator_info, _ModelValidatorDecoratorInfo):
#                 if decorator_info.pre:
#                     model_prevalidators.append(func)
#                 else:
#                     model_postvalidators.append(func)
#         attrs["__fields__"] = fields
#         attrs["__slots__"] = attrs.get("__slots__", tuple()) + tuple(fields)
#         attrs["_preprocessors"] = preprocessors
#         attrs["_postprocessors"] = postprocessors
#         attrs["_model_prevalidators"] = tuple(model_prevalidators)
#         attrs["_model_postvalidators"] = tuple(model_postvalidators)
#         attrs["_field_validators"] = field_validators
#         return super().__new__(tp, classname, bases, attrs)


# _reserved_names.update(dir(ModelMeta))


# MT = TypeVar("MT", bound="Model")


# @IModel.register
# @dataclass_transform(kw_only_default=True)
# class Model(metaclass=ModelMeta):
#     """Base class for models.

#     To create custom model, you simply need to create subclass of this type and
#     declare fields via annotations.

#     This class is a virtual subclass of :class:`IModel` abstract base class.
#     """

#     __slots__ = ("_loc", "_fields_set", "_config")
#     __config__ = Config()

#     def __init__(self, **kwargs):
#         self._loc = Loc()
#         self._fields_set = set()
#         self._config = self.__class__.__config__
#         errors = []
#         fields = self.__class__.__fields__
#         for name, field_info in fields.items():
#             default = field_info.compute_default()
#             try:
#                 setattr(self, name, kwargs.get(name, default))
#             except ParsingError as e:
#                 errors.extend(e.errors)
#         if errors:
#             raise ParsingError(tuple(errors))

#     def __iter__(self) -> Iterator[str]:
#         for field_name in self.__class__.__fields__.keys():
#             if getattr(self, field_name) is not Unset:
#                 yield field_name

#     def __contains__(self, name: str) -> bool:
#         return name in self._fields_set

#     def __repr__(self) -> str:
#         items = (f"{k}={getattr(self, k)!r}" for k in self.__class__.__fields__)
#         return f"{self.__class__.__name__}({', '.join(items)})"

#     def __setattr__(self, name: str, value: Any):
#         cls = self.__class__
#         if name not in cls.__fields__ and name.startswith("_"):
#             return super().__setattr__(name, value)
#         if name not in cls.__fields__:
#             raise AttributeError(f"{cls.__name__!r} model has no field named {name!r}")
#         config = self._config
#         self._fields_set.discard(name)
#         if value is Unset:
#             return super().__setattr__(name, value)
#         loc = self.get_loc() + Loc(name)
#         for preprocessor in cls._preprocessors.get(name, []):
#             value = preprocessor(cls, loc, name, value, config)
#             if isinstance(value, Invalid):
#                 break
#         if not isinstance(value, Invalid):
#             field = cls.__fields__[name]
#             parser = config.type_parser_provider.provide_type_parser(field.type, config)
#             value = parser(value, loc, config)
#         if not isinstance(value, Invalid):
#             for postprocessor in cls._postprocessors.get(name, []):
#                 value = postprocessor(cls, loc, name, value, config)
#                 if isinstance(value, Invalid):
#                     break
#         if isinstance(value, Invalid):
#             raise ParsingError(value.errors)
#         self._fields_set.add(name)
#         super().__setattr__(name, value)

#     def __delattr__(self, name: str) -> None:
#         return self.__setattr__(name, Unset)

#     def __eq__(self, value: object) -> bool:
#         if type(value) is not self.__class__:
#             return False
#         for name in self.__class__.__fields__:
#             if getattr(self, name) != getattr(value, name):
#                 return False
#         return True

#     def __ne__(self, value: object) -> bool:
#         return not self.__eq__(value)

#     def set_config(self, config: IConfig):
#         self._config = config

#     def set_loc(self, loc: Loc):
#         self._loc = loc

#     def get_loc(self) -> Loc:
#         """Get location previously set by :meth:`set_loc` method."""
#         return self._loc

#     def get_value(self, loc: Loc, memo: Optional[dict] = None) -> Optional[Any]:
#         """Get value at given absolute location, or return ``None`` if given
#         *loc* does not point to an existing value.

#         This method can be used to retrieve value from a nested model, nested
#         mapping, nested list or combination of all. Can be used by validators
#         to obtain value from a root model.

#         :param loc:
#             Absolute location of the value.

#         :param memo:
#             Optional dictionary to memoize values found for given *loc*.

#             When this is given and *loc* is missing, then perform full lookup
#             and store result in the memo. When called again with same *loc*,
#             then value from *memo* will be returned.
#         """
#         if memo is None:
#             return _get_model_field_value(self, loc)
#         memoized_value = memo.get(loc, Unset)
#         if memoized_value is not Unset:
#             return memoized_value
#         memo[loc] = value = _get_model_field_value(self, loc)
#         return value

#     def validate(self) -> None:
#         """Validate this model.

#         This runs both built-in and user-defined validators (if any).
#         Validation does not run automatically, so this method must explicitly
#         be called to check if the model is valid.
#         """
#         loc = self.get_loc()
#         errors: List[IError] = []
#         _validate_model(self, loc, errors, self, self.__config__)
#         if errors:
#             raise ValidationError(self, tuple(errors))

#     def dump(self, func: Optional[IDumpFilter] = None) -> dict:
#         """Dump this model to dict.

#         When optional *func* is provided, then use it to filter out unnecessary
#         values or change values that will be placed in the resulting dict.

#         :param func:
#             Filter function.
#         """
#         loc = self.get_loc()
#         func = (lambda v, l: (v, False)) if func is None else func
#         dump_value = _dump_model(self, loc, cast(IDumpFilter, func))
#         return dump_value[0]

#     @classmethod
#     def load(cls: Type[MT], data: dict) -> MT:
#         """Parse given dict into a new instance of this model.

#         This method basically simply calls the constructor with provided data
#         and is added to the interface just to provide API symmetry with the
#         :meth:`dump` method.

#         May raise :exc:`modelity.exc.ParsingError` if *data* could not be
#         parsed into model object.

#         :param data:
#             Dict to be parsed into instance of model.
#         """
#         return cls(**data)

#     @classmethod
#     def load_valid(cls: Type[MT], data: dict) -> MT:
#         """Create model and validate it shortly after.

#         This method was added for convenience to reduce boilerplate code in
#         situations where data is required to be valid.

#         May raise either :exc:`modelity.exc.ParsingError` or
#         :exc:`modelity.exc.ValidationError`.

#         :param `**kwargs`:
#             Keyword args to initialize model with.
#         """
#         obj = cls(**data)
#         obj.validate()
#         return obj


# _reserved_names.update(dir(Model))
