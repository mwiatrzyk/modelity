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
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    cast,
    TypeVar,
)
from typing_extensions import dataclass_transform

from modelity import _utils
from modelity.error import ErrorFactory, Error
from modelity.exc import ParsingError, ValidationError
from modelity.field import BoundField, Field
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.interface import IDumpFilter, ITypeParserProvider
from modelity.providers import CachingTypeParserProviderProxy
from modelity._parsing.type_parsers.all import provider as _root_provider
from modelity.unset import Unset
from modelity.interface import IModel

_reserved_names: Set[str] = set()
_order_id = itertools.count()


class _DecoratorInfo:
    __slots__ = ("ordering_id",)

    ordering_id: int

    def __init__(self):
        self.ordering_id = next(_order_id)


class _ProcessorDecoratorInfo(_DecoratorInfo):
    __slots__ = ("type", "field_names")

    class Type(enum.Enum):
        PRE = 1
        POST = 2

    type: Type
    field_names: Tuple[str, ...]

    def __init__(self, type: Type, field_names: Tuple[str, ...]):
        super().__init__()
        self.type = type
        self.field_names = field_names


class _FieldValidatorDecoratorInfo(_DecoratorInfo):
    __slots__ = ("field_names",)

    field_names: Tuple[str, ...]

    def __init__(self, field_names: Tuple[str, ...]):
        super().__init__()
        self.field_names = field_names


class _ModelValidatorDecoratorInfo(_DecoratorInfo):
    __slots__ = ("pre",)

    pre: bool

    def __init__(self, pre: bool):
        super().__init__()
        self.pre = pre


def _wrap_field_processor(func: Callable):

    @functools.wraps(func)
    def proxy(cls: Type["Model"], loc: Loc, name: str, value: Any) -> Union[Any, Invalid]:
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


def _dump_model(value: "Model", loc: Loc, func: IDumpFilter) -> Tuple[dict, bool]:
    result = {}
    for field_name in value.__class__.__fields__:
        dump_value, skip = _dump_any(getattr(value, field_name), loc + Loc(field_name), func)
        if not skip:
            result[field_name] = dump_value
    return result, False


def _dump_any(value: Any, loc: Loc, func: IDumpFilter) -> Tuple[Any, bool]:
    value, skip = func(value, loc)
    if skip:
        return value, skip
    if type(value) in (str, bytes, bytearray):  # Exception, to avoid infinite recursion (these are sequences)
        return value, False
    if isinstance(value, Model):
        return _dump_model(value, loc, func)
    if isinstance(value, Mapping):
        return _dump_mapping(value, loc, func)
    if isinstance(value, Sequence):
        return _dump_sequence(value, loc, func)
    return value, False


def _dump_mapping(value: Mapping, loc: Loc, func: IDumpFilter) -> Tuple[dict, bool]:
    result = {}
    for key, value in value.items():
        dump_value, skip = _dump_any(value, loc + Loc(key), func)
        if not skip:
            result[key] = dump_value
    return result, False


def _dump_sequence(value: Sequence, loc: Loc, func: IDumpFilter) -> Tuple[list, bool]:
    result = []
    for i, value in enumerate(value):
        dump_value, skip = _dump_any(value, loc + Loc(i), func)
        if not skip:
            result.append(dump_value)
    return result, False


def _validate_model(obj: "Model", loc: Loc, errors: List[Error], root: "Model"):
    cls = obj.__class__
    for model_validator in cls._model_prevalidators:
        errors.extend(model_validator(cls, obj, root, errors))
    for name, field_info in cls.__fields__.items():
        field_loc = loc + Loc(name)
        value = getattr(obj, name)
        if value is Unset:
            if field_info.is_required():
                errors.append(ErrorFactory.required_missing(loc + Loc(name)))
            continue
        _validate_any(value, field_loc, errors, root)
        for field_validator in cls._field_validators.get(name, []):
            errors.extend(field_validator(cls, obj, root, name, value))
    for model_validator in cls._model_postvalidators:
        errors.extend(model_validator(cls, obj, root, errors))


def _validate_any(obj: Any, loc: Loc, errors: List[Error], root: "Model"):
    if isinstance(obj, IModel):
        _validate_model(cast(Model, obj), loc, errors, root)
    elif isinstance(obj, Mapping):
        for k, v in obj.items():
            _validate_any(v, loc + Loc(k), errors, root)
    elif isinstance(obj, Sequence) and type(obj) not in (str, bytes, bytearray):
        for i, v in enumerate(obj):
            _validate_any(v, loc + Loc(i), errors, root)


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

    def decorator(func):

        @functools.wraps(func)
        def proxy(cls: Type["Model"], self: "Model", root: "Model", name: str, value: Any):
            kw: Dict[str, Any] = {}
            if "cls" in given_params:
                kw["cls"] = cls
            if "self" in given_params:
                kw["self"] = self
            if "root" in given_params:
                kw["root"] = root
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
            model_loc = self.get_loc()
            if isinstance(result, Error):
                return (Error(model_loc + Loc(name) + result.loc, result.code, result.data),)
            return tuple(Error(model_loc + Loc(name) + e.loc, e.code, e.data) for e in cast(Iterable[Error], result))

        sig = inspect.signature(func)
        supported_params = ("cls", "self", "root", "name", "value")
        given_params = tuple(sig.parameters)
        if not _utils.is_subsequence(given_params, supported_params):
            raise TypeError(
                f"incorrect field validator's signature; {_utils.format_signature(given_params)} is not a subsequence of {_utils.format_signature(supported_params)}"
            )
        proxy.__modelity_decorator_info__ = _FieldValidatorDecoratorInfo(field_names)
        return proxy

    return decorator


def model_validator(pre: bool = False):
    """Decorate custom function as model validator.

    Unlike field validators, model validators run for entire models, as a final
    validation step, after all other validators.

    Decorated function can have any number of arguments declared, but those must
    be named and ordered as depicted in :meth:`IModelValidator.__call__` method
    description.

    :param pre:
        Run this validator before any other validators.
    """

    def decorator(func):

        @functools.wraps(func)
        def proxy(cls: Type["Model"], self: "Model", root: "Model", errors: List[Error]):
            kw: Dict[str, Any] = {}
            if "cls" in given_params:
                kw["cls"] = cls
            if "self" in given_params:
                kw["self"] = self
            if "root" in given_params:
                kw["root"] = root
            if "errors" in given_params:
                kw["errors"] = errors
            try:
                result = func(**kw)
            except ValueError as e:
                result = ErrorFactory.value_error(Loc(), str(e))
            except TypeError as e:
                result = ErrorFactory.type_error(Loc(), str(e))
            if result is None:
                return tuple()
            model_loc = self.get_loc()
            if isinstance(result, Error):
                return (Error(model_loc + result.loc, result.code, result.data),)
            return tuple(Error(model_loc + e.loc, e.code, e.data) for e in cast(Iterable[Error], result))

        sig = inspect.signature(func)
        given_params = tuple(sig.parameters)
        supported_params = ("cls", "self", "root", "errors")
        if not _utils.is_subsequence(given_params, supported_params):
            raise TypeError(
                f"model validator {func.__name__!r} has incorrect signature: {_utils.format_signature(given_params)} is not a subsequence of {_utils.format_signature(supported_params)}"
            )
        proxy.__modelity_decorator_info__ = _ModelValidatorDecoratorInfo(pre)
        return proxy

    return decorator


def preprocessor(*field_names: str):
    """Decorate a function as a field value preprocessor.

    Preprocessors are called when value is set, before type parsing takes
    place. The role of preprocessors is to perform input data filtering for
    further steps like type parsing and postprocessors.

    :param `*field_names`:
        List of field names this preprocessor will be called for.

        If not set, then it will be called for every field.
    """

    def decorator(func: Callable):
        proxy = _wrap_field_processor(func)
        proxy.__modelity_decorator_info__ = _ProcessorDecoratorInfo(_ProcessorDecoratorInfo.Type.PRE, field_names)
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

    def decorator(func: Callable):
        proxy = _wrap_field_processor(func)
        proxy.__modelity_decorator_info__ = _ProcessorDecoratorInfo(_ProcessorDecoratorInfo.Type.POST, field_names)
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


def get_builtin_type_parser_provider() -> ITypeParserProvider:
    """Get instance of :class:`ITypeParserProvider` class containing all built-in
    type parsers.

    This can be used to add custom types simply by creating custom type parser
    provider and attaching this one to add built-in types.
    """
    return _root_provider


@dataclasses.dataclass()
class ModelConfig:
    """Model configuration object.

    Custom instances or subclasses are allowed to be set via
    :attr:`Model.__config__` attribute.
    """

    #: Provider used to find type parser.
    #:
    #: Can be customized to allow user-defined type to be used by the library.
    type_parser_provider: ITypeParserProvider = dataclasses.field(
        default_factory=lambda: CachingTypeParserProviderProxy(get_builtin_type_parser_provider())
    )

    #: Placeholder for user-defined data.
    user_data: dict = dataclasses.field(default_factory=dict)


class ModelMeta(type):
    """Metaclass for :class:`Model` class."""

    __config__: ModelConfig
    __fields__: Mapping[str, BoundField]
    _preprocessors: Mapping[str, Sequence[Callable]]
    _postprocessors: Mapping[str, Sequence[Callable]]
    _field_validators: Mapping[str, Sequence[Callable]]
    _model_prevalidators: Sequence[Callable]
    _model_postvalidators: Sequence[Callable]

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
                    if callable(attr_value) and hasattr(attr_value, "__modelity_decorator_info__"):
                        yield attr_value

        def iter_decorators() -> Iterator[Tuple[Callable, _DecoratorInfo]]:
            for obj in itertools.chain(inherit_decorators(), attrs.values()):
                if callable(obj):
                    decorator_info = getattr(obj, "__modelity_decorator_info__", None)
                    if decorator_info is not None:
                        yield obj, decorator_info

        fields = dict(inherit_fields())
        for field_name, type in itertools.chain(
            inherit_mixed_in_annotations(), attrs.get("__annotations__", {}).items()
        ):
            if field_name in _reserved_names:
                raise TypeError(f"the name {field_name!r} is reserved by Modelity and cannot be used as field name")
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
        preprocessors: Dict[str, List[Callable]] = {}
        postprocessors: Dict[str, List[Callable]] = {}
        model_prevalidators: List[Callable] = []
        model_postvalidators: List[Callable] = []
        field_validators: Dict[str, List[Callable]] = {}
        for func, decorator_info in sorted(iter_decorators(), key=lambda x: x[1].ordering_id):
            if isinstance(decorator_info, _ProcessorDecoratorInfo):
                target_map = (
                    preprocessors if decorator_info.type == _ProcessorDecoratorInfo.Type.PRE else postprocessors
                )
                for field_name in decorator_info.field_names or fields:
                    target_map.setdefault(field_name, []).append(func)
            elif isinstance(decorator_info, _FieldValidatorDecoratorInfo):
                for field_name in decorator_info.field_names or fields:
                    field_validators.setdefault(field_name, []).append(func)
            elif isinstance(decorator_info, _ModelValidatorDecoratorInfo):
                if decorator_info.pre:
                    model_prevalidators.append(func)
                else:
                    model_postvalidators.append(func)
        attrs["__fields__"] = fields
        attrs["__slots__"] = attrs.get("__slots__", tuple()) + tuple(fields)
        attrs["_preprocessors"] = preprocessors
        attrs["_postprocessors"] = postprocessors
        attrs["_model_prevalidators"] = tuple(model_prevalidators)
        attrs["_model_postvalidators"] = tuple(model_postvalidators)
        attrs["_field_validators"] = field_validators
        return super().__new__(tp, classname, bases, attrs)


_reserved_names.update(dir(ModelMeta))


MT = TypeVar("MT", bound="Model")


@IModel.register
@dataclass_transform(kw_only_default=True)
class Model(metaclass=ModelMeta):
    """Base class for models.

    To create custom model, you simply need to create subclass of this type and
    declare fields via annotations.
    """

    __slots__ = ("_loc", "_fields_set")
    __config__ = ModelConfig()

    def __init__(self, **kwargs):
        self._loc = Loc()
        self._fields_set = set()
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

    def __iter__(self) -> Iterator[str]:
        for field_name in self.__class__.__fields__.keys():
            if field_name in self._fields_set:
                yield field_name

    def __contains__(self, name: str) -> bool:
        return name in self._fields_set

    def __repr__(self) -> str:
        items = (f"{k}={getattr(self, k)!r}" for k in self.__class__.__fields__)
        return f"{self.__class__.__name__}({', '.join(items)})"

    def __setattr__(self, name: str, value: Any):
        cls = self.__class__
        if name not in cls.__fields__ and name.startswith("_"):
            return super().__setattr__(name, value)
        if name not in cls.__fields__:
            raise AttributeError(f"model {cls.__name__!r} has no field named {name!r}")
        self._fields_set.discard(name)
        if value is Unset:
            return super().__setattr__(name, value)
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
        self._fields_set.add(name)
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        return self.__setattr__(name, Unset)

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
        """Set location of this model.

        This is used when this model is nested inside another model, to give it
        the location that is later used to render proper error messages.

        :param loc:
            The location to be set.
        """
        self._loc = loc

    def get_loc(self) -> Loc:
        """Get location previously set by :meth:`set_loc` method."""
        return self._loc

    def validate(self) -> None:
        """Validate this model.

        This runs both built-in and user-defined validators (if any).
        Validation does not run automatically, so this method must explicitly
        be called to check if the model is valid.
        """
        loc = self.get_loc()
        errors: List[Error] = []
        _validate_model(self, loc, errors, self)
        if errors:
            raise ValidationError(self, tuple(errors))

    def dump(self, func: Optional[IDumpFilter] = None) -> dict:
        """Dump this model to dict.

        When optional *func* is provided, then use it to filter out unnecessary
        values or change values that will be placed in the resulting dict.

        :param func:
            Filter function.
        """
        loc = self.get_loc()
        func = (lambda v, l: (v, False)) if func is None else func
        dump_value = _dump_model(self, loc, cast(IDumpFilter, func))
        return dump_value[0]

    @classmethod
    def load(cls: Type[MT], data: dict) -> MT:
        """Parse given dict into a new instance of this model.

        This method basically simply calls the constructor with provided data
        and is added to the interface just to provide API symmetry with the
        :meth:`dump` method.

        May raise :exc:`modelity.exc.ParsingError` if *data* could not be
        parsed into model object.

        :param data:
            Dict to be parsed into instance of model.
        """
        return cls(**data)

    @classmethod
    def create_valid(cls: Type[MT], **kwargs) -> MT:
        """Create model and validate it shortly after.

        This method was added for convenience to reduce boilerplate code in
        situations where data is required to be valid.

        May raise either :exc:`modelity.exc.ParsingError` or
        :exc:`modelity.exc.ValidationError`.

        :param `**kwargs`:
            Keyword args to initialize model with.
        """
        obj = cls(**kwargs)
        obj.validate()
        return obj


_reserved_names.update(dir(Model))
