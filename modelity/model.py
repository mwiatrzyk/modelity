import enum
import functools
import inspect
import itertools
import dataclasses
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)
from typing_extensions import dataclass_transform

from modelity import _utils
from modelity.error import ErrorFactory, Error
from modelity.exc import ParsingError, ValidationError
from modelity.field import BoundField, Field
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.interface import IModelConfig, IModelMeta, ITypeParserProvider
from modelity.parsing.providers import CachingTypeParserProviderProxy
from modelity.parsing.type_parsers.all import provider
from modelity.unset import Unset, UnsetType
from modelity.interface import IModel, IModelValidator, IFieldValidator, IFieldProcessor

_model_special_attrs = ("_loc",)
_reserved_field_names = tuple(IModelMeta.__annotations__)


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


def _wrap_field_processor(func: Callable) -> IFieldProcessor:

    @functools.wraps(func)
    def proxy(cls: Type[IModel], loc: Loc, name: str, value: Any) -> Union[Any, Invalid]:
        kw: Dict[str, Any] = {}
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


def field_validator(*field_names: str):
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

    def decorator(func) -> IFieldValidator:

        @functools.wraps(func)
        def proxy(cls: Type[IModel], model: IModel, name: str, value: Any):
            kw: Dict[str, Any] = {}
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
            return tuple(Error(model_loc + Loc(name) + e.loc, e.code, e.data) for e in cast(Iterable[Error], result))

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
    def proxy(cls, model: IModel, errors: Tuple[Error, ...], root_model: Optional[IModel] = None):
        kw: Dict[str, Any] = {}
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
        return tuple(Error(model_loc + e.loc, e.code, e.data) for e in cast(Iterable[Error], result))

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
    """Decorate a function as a field value preprocessor.

    Preprocessors are called when value is set, before type parsing takes
    place. The role of preprocessors is to perform input data filtering for
    further steps like type parsing and postprocessors.

    :param `*field_names`:
        List of field names this preprocessor will be called for.

        If not set, then it will be called for every field.
    """

    def decorator(func: Callable) -> IFieldProcessor:
        proxy = _wrap_field_processor(func)
        _DecoratorInfo.assign_to_object(proxy, _DecoratorInfo.Type.PREPROCESSOR, field_names=field_names)
        return proxy

    return decorator


def postprocessor(*field_names: str):
    """Decorate a function as a field value postprocessor.

    Postprocessors are called after preprocessors and type parsing, therefore
    it can be assumed that a value is of valid type when postprocessors are
    called.

    :param `*field_names`:
        List of field names this postprocessor will be called for.

        If left empty, then it will be called for every field.
    """

    def decorator(func: Callable) -> IFieldProcessor:
        proxy = _wrap_field_processor(func)
        _DecoratorInfo.assign_to_object(proxy, _DecoratorInfo.Type.POSTPROCESSOR, field_names=field_names)
        return proxy

    return decorator


def field(default: Any = Unset, optional: bool = False) -> "Field":
    """Helper used to declare additional metadata for model field.

    :param default:
        Field's default value.

    :param optional:
        Flag telling that the field is optional.

        This can be used to declare fields that can either be set to given type
        or not set at all, as opposed to :class:`typing.Optional`, which is
        defacto an union of type ``T`` and ``NoneType``.
    """
    return Field(default=default, optional=optional)


@dataclasses.dataclass()
class ModelConfig(IModelConfig):
    """Model configuration object.

    Custom instances or subclasses are allowed to be set via
    :attr:`Model.__config__` attribute.
    """

    #: Provider used to find type parser.
    #:
    #: Can be customized to allow user-defined type to be used by the library.
    type_parser_provider: ITypeParserProvider = CachingTypeParserProviderProxy(provider)

    #: Placeholder for user-defined data.
    user_data: dict = dataclasses.field(default_factory=dict)


class ModelMeta(IModelMeta):
    """Metaclass for :class:`Model` class."""

    _preprocessors: Mapping[str, Sequence[IFieldProcessor]]
    _postprocessors: Mapping[str, Sequence[IFieldProcessor]]
    _field_validators: Mapping[str, Sequence[IFieldValidator]]
    _model_validators: Sequence[IModelValidator]

    def __new__(tp, classname: str, bases: Tuple[Type], attrs: dict):

        def inherit_config() -> Optional[ModelConfig]:
            for b in bases:
                if isinstance(b, ModelMeta):
                    return b.__config__
            return None

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
            if field_name in _reserved_field_names:
                continue
            field_info = attrs.pop(field_name, None)
            if field_info is None:
                field_info = BoundField(field_name, type)
            elif isinstance(field_info, Field):
                field_info = BoundField(
                    field_name,
                    type,
                    default=field_info.default,
                    optional=field_info.optional,
                )
            else:
                field_info = BoundField(field_name, type, default=field_info)
            fields[field_name] = field_info
        preprocessors: Dict[str, List[IFieldProcessor]] = {}
        postprocessors: Dict[str, List[IFieldProcessor]] = {}
        model_validators: List[IModelValidator] = []
        field_validators: Dict[str, List[IFieldValidator]] = {}
        for attr_value in itertools.chain(inherit_decorators(), attrs.values()):
            decorator_info = _DecoratorInfo.extract_from_object(attr_value)
            if decorator_info is None:
                continue
            if decorator_info.type in (_DecoratorInfo.Type.PREPROCESSOR, _DecoratorInfo.Type.POSTPROCESSOR):
                target_map = (
                    preprocessors if decorator_info.type == _DecoratorInfo.Type.PREPROCESSOR else postprocessors
                )
                for field_name in decorator_info.params.get("field_names", []) or fields:
                    target_map.setdefault(field_name, []).append(attr_value)
            elif decorator_info.type == _DecoratorInfo.Type.MODEL_VALIDATOR:
                model_validators.append(attr_value)
            elif decorator_info.type == _DecoratorInfo.Type.FIELD_VALIDATOR:
                for field_name in decorator_info.params.get("field_names", []) or fields:
                    field_validators.setdefault(field_name, []).append(attr_value)
        attrs["__fields__"] = fields
        attrs["__slots__"] = _model_special_attrs + tuple(fields)
        attrs["__config__"] = attrs.get("__config__", inherit_config() or ModelConfig())
        attrs["_preprocessors"] = preprocessors
        attrs["_postprocessors"] = postprocessors
        attrs["_model_validators"] = tuple(model_validators)
        attrs["_field_validators"] = field_validators
        return super().__new__(tp, classname, bases, attrs)


@dataclass_transform(kw_only_default=True)
class Model(IModel, metaclass=ModelMeta):
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
        if value is Unset or name in _model_special_attrs:
            return super().__setattr__(name, value)
        cls = self.__class__
        loc = self.get_loc() + Loc(name)
        for preprocessor in cls._preprocessors.get(name, []):
            value = preprocessor(cls, loc, name, value)
            if isinstance(value, Invalid):
                break
        if not isinstance(value, Invalid):
            field = cls.__fields__[name]
            parser = cls.__config__.type_parser_provider.provide_type_parser(field.type)
            value = parser(value, self._loc + Loc(name))
        if not isinstance(value, Invalid):
            for postprocessor in cls._postprocessors.get(name, []):
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

    def validate(self, root_model: Optional[IModel] = None):
        cls = self.__class__
        root_model = self if root_model is None else root_model  # type: ignore
        errors = []
        self_loc = self.get_loc()
        for name, field_info in cls.__fields__.items():
            value = getattr(self, name)
            if value is Unset:
                if field_info.is_required():
                    errors.append(ErrorFactory.required_missing(self_loc + Loc(name)))
                continue
            if isinstance(value, IModel):
                try:
                    value.validate(root_model)
                except ValidationError as e:
                    errors.extend(e.errors)
            for field_validator in cls._field_validators.get(name, []):
                errors.extend(field_validator(cls, self, name, value))
        for model_validator in cls._model_validators:
            errors.extend(model_validator(cls, self, tuple(errors), root_model=root_model))
        if errors:
            raise ValidationError(self, tuple(errors))
