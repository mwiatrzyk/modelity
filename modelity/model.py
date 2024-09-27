import dataclasses
import enum
import functools
import inspect
import itertools
from typing import Any, Callable, Mapping, Optional, Sequence, Tuple, Type, Union, get_args, get_origin
from typing_extensions import dataclass_transform

from modelity import _utils
from modelity.error import ErrorFactory, Error
from modelity.exc import ParsingError, ValidationError
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.parsing.interface import IParserProvider
from modelity.parsing.parsers.all import registry
from modelity.undefined import Undefined
from modelity.interface import IModel, IModelValidator, IFieldValidator, IFieldProcessor

_model_special_attrs = ("_loc",)


@dataclasses.dataclass(frozen=True)
class _DecoratorInfo:

    class Type(enum.Enum):
        PREPROCESSOR = 1
        POSTPROCESSOR = 2
        FIELD_VALIDATOR = 3
        MODEL_VALIDATOR = 4

    type: Type
    params: dict

    @classmethod
    def create(cls, type: Type, **params: Any) -> "_DecoratorInfo":
        return cls(type, params)

    @classmethod
    def assign_to_object(cls, obj: object, type: Type, **params: Any):
        setattr(obj, "__modelity_decorator__", cls.create(type, **params))

    @staticmethod
    def extract_from_object(obj: object) -> Optional["_DecoratorInfo"]:
        return getattr(obj, "__modelity_decorator__", None)


def field_validator(*field_names: str) -> IFieldValidator:
    """Decorate custom function as a field validator.

    Field validators are executed only if field has value assigned, implying
    that the value has correct type (as it has to be successfully parsed
    first).

    Decorated function can have any number of arguments declared, but those must
    be named and ordered as depicted in :meth:`IFieldValidator.__call__` method.

    :param `*field_names`:
        Names of fields to run this validator for.

        If none given, then it will run for all fields in a model it is declared in.
    """

    def decorator(func):

        @functools.wraps(func)
        def proxy(cls: Type[IModel], model: IModel, name: str, value: Any):
            kw = {}
            if "cls" in given_params:
                kw["cls"] = cls
            if "model" in given_params:
                kw["model"] = model
            if "name" in given_params:
                kw["name"] = name
            if "value" in given_params:
                kw["value"] = value
            try:
                result = func(**kw)
            except ValueError as e:
                result = ErrorFactory.value_error(Loc(), str(e))
            except TypeError as e:
                result = ErrorFactory.type_error(Loc(), str(e))
            if result is None:
                return tuple()
            model_loc = model.get_loc()
            if isinstance(result, Error):
                return (Error(model_loc + Loc(name) + result.loc, result.code, result.data),)
            result: Sequence[Error] = result
            return tuple(Error(model_loc + Loc(name) + e.loc, e.code, e.data) for e in result)

        sig = inspect.signature(func)
        supported_params = ("cls", "model", "name", "value")
        given_params = tuple(sig.parameters)
        if not _utils.is_subsequence(given_params, supported_params):
            raise TypeError(
                f"incorrect field validator's signature; {_utils.format_signature(given_params)} is not a subsequence of {_utils.format_signature(supported_params)}"
            )
        _DecoratorInfo.assign_to_object(proxy, _DecoratorInfo.Type.FIELD_VALIDATOR, field_names=field_names)
        return proxy

    return decorator


def model_validator(func: Callable) -> IModelValidator:
    """Decorate custom function as model validator.

    Unlike field validators, model validators run for entire models, as a final
    validation step, after all other validators.

    Decorated function can have any number of arguments declared, but those must
    be named and ordered as depicted in :meth:`IModelValidator.__call__` method
    description.
    """

    @functools.wraps(func)
    def proxy(cls, model: IModel, errors: Tuple[Error, ...], root_model: IModel = None):
        kw = {}
        if "cls" in given_params:
            kw["cls"] = cls
        if "model" in given_params:
            kw["model"] = model
        if "errors" in given_params:
            kw["errors"] = errors
        if "root_model" in given_params:
            kw["root_model"] = root_model
        try:
            result = func(**kw)
        except ValueError as e:
            result = ErrorFactory.value_error(Loc(), str(e))
        except TypeError as e:
            result = ErrorFactory.type_error(Loc(), str(e))
        if result is None:
            return tuple()
        model_loc = model.get_loc()
        if isinstance(result, Error):
            return (Error(model_loc + result.loc, result.code, result.data),)
        result: Sequence[Error] = result
        return tuple(Error(model_loc + e.loc, e.code, e.data) for e in result)

    sig = inspect.signature(func)
    given_params = tuple(sig.parameters)
    supported_params = ("cls", "model", "errors", "root_model")
    if not _utils.is_subsequence(given_params, supported_params):
        raise TypeError(
            f"model validator {func.__name__!r} has incorrect signature: {_utils.format_signature(given_params)} is not a subsequence of {_utils.format_signature(supported_params)}"
        )
    _DecoratorInfo.assign_to_object(proxy, _DecoratorInfo.Type.MODEL_VALIDATOR)
    return proxy


def preprocessor(*field_names: str):

    def decorator(func: Callable):
        proxy = wrap_field_processor(func)
        _DecoratorInfo.assign_to_object(proxy, _DecoratorInfo.Type.PREPROCESSOR, field_names=field_names)
        return proxy

    return decorator


def postprocessor(*field_names: str):

    def decorator(func: Callable) -> IFieldProcessor:
        proxy = wrap_field_processor(func)
        _DecoratorInfo.assign_to_object(proxy, _DecoratorInfo.Type.POSTPROCESSOR, field_names=field_names)
        return proxy

    return decorator


def wrap_field_processor(func: Callable) -> IFieldProcessor:

    @functools.wraps(func)
    def proxy(cls: Type[IModel], loc: Loc, name: str, value: Any) -> Union[Any, Invalid]:
        kw = {}
        if "cls" in given_params:
            kw["cls"] = cls
        if "loc" in given_params:
            kw["loc"] = loc
        if "name" in given_params:
            kw["name"] = name
        if "value" in given_params:
            kw["value"] = value
        try:
            result = func(**kw)
        except ValueError as e:
            return Invalid(value, ErrorFactory.value_error(loc, str(e)))
        except TypeError as e:
            return Invalid(value, ErrorFactory.type_error(loc, str(e)))
        if isinstance(result, Invalid):
            return Invalid(result.value, *(Error(loc + e.loc, e.code, e.data) for e in result.errors))
        return result

    sig = inspect.signature(func)
    given_params = tuple(sig.parameters)
    supported_params = ("cls", "loc", "name", "value")
    if not _utils.is_subsequence(given_params, supported_params):
        raise TypeError(
            f"field processor {func.__name__!r} has incorrect signature: {_utils.format_signature(given_params)} is not a subsequence of {_utils.format_signature(supported_params)}"
        )
    return proxy


def field(default: Any = Undefined, optional: bool = False) -> "FieldInfo":
    """Helper used to declare additional metadata for model field.

    :param default:
        Field's default value.

    :param optional:
        Flag telling that the field is optional.

        This can be used to declare fields that can either be set to given type
        or not set at all, as opposed to :class:`typing.Optional`, which is
        defacto an union of type ``T`` and ``NoneType``.
    """
    return FieldInfo(default=default, optional=optional)


@dataclasses.dataclass(frozen=True, eq=False, repr=False, slots=True)
class FieldInfo:
    """Object containing field metadata.

    Objects of this type are automatically created from type annotations, but
    can also be created explicitly to override field defaults (see :meth:`field`
    for details).
    """

    #: Field's name.
    name: str = Undefined

    #: Field's full type.
    type: Type = Undefined

    #: Field's type origin.
    #:
    #: For example, if :attr:`type` is ``List[str]``, then this will be set to ``list``.
    type_origin: Optional[Type] = None

    #: Field's type args.
    #:
    #: For example, if :attr:`type` is ``Dict[str, int]``, then this will be set
    #: to ``(str, int)`` tuple.
    type_args: tuple = tuple()

    #: Field's default value.
    default: Any = Undefined

    #: Flag telling if this field is optional.
    #:
    #: Normally, you should use :class:`typing.Optional` to indicate that the
    #: field is optional. However, field declared like that allow ``None`` to be
    #: explicitly set. If you need to indicate that the field is optional, but
    #: to also disallow ``None`` as the valid value, then this is the option
    #: you'll need.
    optional: bool = False

    def __repr__(self) -> str:
        return f"<{self.__module__}.{self.__class__.__qualname__}(name={self.name!r}, type={self.type!r}, default={self.default!r})>"

    def __eq__(self, value: object) -> bool:
        if type(value) is not FieldInfo:
            return False
        return self.name == value.name and self.type == value.type and self.default == value.default

    def __ne__(self, value: object) -> bool:
        return not self.__eq__(value)

    def is_optional(self):
        """Check if this field is optional."""
        return self.optional or self.default is not Undefined or type(None) in self.type_args

    def is_required(self):
        """Check if this field is required.

        This is simply a negation of :meth:`is_optional` method.
        """
        return not self.is_optional()

    def compute_default(self) -> Any:
        """Compute default value for this field."""
        return self.default


@dataclasses.dataclass
class ModelConfig:
    parser_provider: IParserProvider = registry


class ModelMeta(type):
    """Metaclass for :class:`Model` class."""

    __fields__: Mapping[str, FieldInfo]
    __config__: ModelConfig
    __preprocessors__: Mapping[str, Sequence[IFieldProcessor]]
    __postprocessors__: Mapping[str, Sequence[IFieldProcessor]]
    __field_validators__: Mapping[str, Sequence[IFieldValidator]]
    __model_validators__: Sequence[IModelValidator]

    def __new__(tp, classname: str, bases: Tuple[Type], attrs: dict):

        def inherit_fields():
            for b in bases:
                yield from getattr(b, "__fields__", {}).items()

        def inherit_mixed_in_annotations():
            for b in filter(lambda b: not isinstance(b, ModelMeta), bases):
                yield from getattr(b, "__annotations__", {}).items()

        def inherit_decorators():
            for b in bases:
                for attr_name in dir(b):
                    attr_value = getattr(b, attr_name)
                    decorator_info = _DecoratorInfo.extract_from_object(attr_value)
                    if decorator_info is not None:
                        yield attr_value

        fields = dict(inherit_fields())
        for field_name, type in itertools.chain(
            inherit_mixed_in_annotations(), attrs.get("__annotations__", {}).items()
        ):
            type_origin = get_origin(type)
            type_args = get_args(type)
            field_info = attrs.pop(field_name, None)
            if field_info is None:
                field_info = FieldInfo(field_name, type, type_origin, type_args)
            elif isinstance(field_info, FieldInfo):
                field_info = FieldInfo(
                    field_name, type, type_origin, type_args, default=field_info.default, optional=field_info.optional
                )
            else:
                field_info = FieldInfo(field_name, type, type_origin, type_args, default=field_info)
            fields[field_name] = field_info
        preprocessors = {}
        postprocessors = {}
        model_validators = []
        field_validators = {}
        for attr_value in itertools.chain(inherit_decorators(), attrs.values()):
            decorator_info = _DecoratorInfo.extract_from_object(attr_value)
            if decorator_info is None:
                continue
            if decorator_info.type in (_DecoratorInfo.Type.PREPROCESSOR, _DecoratorInfo.Type.POSTPROCESSOR):
                target_map = preprocessors if decorator_info.type == _DecoratorInfo.Type.PREPROCESSOR else postprocessors
                for field_name in decorator_info.params.get("field_names", []) or fields:
                    target_map.setdefault(field_name, []).append(attr_value)
            elif decorator_info.type == _DecoratorInfo.Type.MODEL_VALIDATOR:
                model_validators.append(attr_value)
            elif decorator_info.type == _DecoratorInfo.Type.FIELD_VALIDATOR:
                for field_name in decorator_info.params.get("field_names", []) or fields:
                    field_validators.setdefault(field_name, []).append(attr_value)
        attrs["__fields__"] = fields
        attrs["__slots__"] = _model_special_attrs + tuple(fields)
        attrs["__config__"] = ModelConfig()
        attrs["__preprocessors__"] = preprocessors
        attrs["__postprocessors__"] = postprocessors
        attrs["__model_validators__"] = tuple(model_validators)
        attrs["__field_validators__"] = field_validators
        return super().__new__(tp, classname, bases, attrs)


@IModel.register
@dataclass_transform(kw_only_default=True)
class Model(metaclass=ModelMeta):
    """Base class for models.

    To create custom model, you simply need to create subclass of this type and
    declare fields via annotations.
    """

    def __init__(self, **kwargs):
        self._loc = Loc()
        errors = []
        fields = self.__class__.__fields__
        for name, field_info in fields.items():
            default = field_info.compute_default()
            try:
                setattr(self, name, kwargs.get(name, default))
            except ParsingError as e:
                errors.extend(e.errors)
        if errors:
            raise ParsingError(tuple(errors))

    def __repr__(self) -> str:
        items = (f"{k}={getattr(self, k)!r}" for k in self.__class__.__fields__)
        return f"{self.__class__.__name__}({', '.join(items)})"

    def __setattr__(self, name: str, value: Any):
        if value is Undefined or name in _model_special_attrs:
            return super().__setattr__(name, value)
        cls = self.__class__
        loc = self.get_loc() + Loc(name)
        for preprocessor in cls.__preprocessors__.get(name, []):
            value = preprocessor(cls, loc, name, value)
            if isinstance(value, Invalid):
                break
        if not isinstance(value, Invalid):
            field = cls.__fields__[name]
            parser = cls.__config__.parser_provider.provide_parser(field.type)
            value = parser(value, self._loc + Loc(name))
        if not isinstance(value, Invalid):
            for postprocessor in cls.__postprocessors__.get(name, []):
                value = postprocessor(cls, loc, name, value)
                if isinstance(value, Invalid):
                    break
        if isinstance(value, Invalid):
            raise ParsingError(value.errors)
        super().__setattr__(name, value)

    def __eq__(self, value: object) -> bool:
        if type(value) is not self.__class__:
            return False
        for name in self.__class__.__fields__:
            if getattr(self, name) != getattr(value, name):
                return False
        return True

    def __ne__(self, value: object) -> bool:
        return not self.__eq__(value)

    def set_loc(self, loc: Loc):
        self._loc = loc

    def get_loc(self) -> Loc:
        return self._loc

    def validate(self, root_model: IModel = None):
        cls = self.__class__
        root_model = self if root_model is None else root_model
        errors = []
        self_loc = self.get_loc()
        for name, field_info in cls.__fields__.items():
            value = getattr(self, name)
            if value is Undefined:
                if field_info.is_required():
                    errors.append(ErrorFactory.required_missing(self_loc + Loc(name)))
                continue
            if isinstance(value, IModel):
                try:
                    value.validate(root_model)
                except ValidationError as e:
                    errors.extend(e.errors)
            for validator in cls.__field_validators__.get(name, []):
                errors.extend(validator(cls, self, name, value))
        for validator in cls.__model_validators__:
            errors.extend(validator(cls, self, tuple(errors), root_model=root_model))
        if errors:
            raise ValidationError(self, tuple(errors))
