import dataclasses
from typing import Any, Mapping, Type, get_args
from typing_extensions import dataclass_transform

from modelity.error import ErrorFactory
from modelity.exc import ParsingError, ValidationError
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.parsing.interface import IParserProvider
from modelity.parsing.parsers.all import registry
from modelity.undefined import Undefined


def field(default: Any = Undefined, optional: bool=False) -> "FieldInfo":
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


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
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
        return self.optional or\
            self.default is not Undefined or\
            type(None) in get_args(self.type)

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

    def __new__(tp, classname, bases, attrs):

        def iter_inherited_fields():
            for b in bases:
                yield from getattr(b, "__fields__", {}).items()

        def iter_annotations():
            for b in bases:
                if not isinstance(b, ModelMeta):
                    yield from getattr(b, "__annotations__", {}).items()
            yield from attrs.get("__annotations__", {}).items()

        fields = dict(iter_inherited_fields())
        for field_name, annotation in iter_annotations():
            field_info = attrs.pop(field_name, None)
            if field_info is None:
                field_info = FieldInfo(field_name, annotation)
            elif isinstance(field_info, FieldInfo):
                field_info = FieldInfo(field_name, annotation, default=field_info.default, optional=field_info.optional)
            else:
                field_info = FieldInfo(field_name, annotation, default=field_info)
            fields[field_name] = field_info
        attrs["__fields__"] = fields
        attrs["__slots__"] = tuple(fields)
        attrs["__config__"] = ModelConfig()
        return super().__new__(tp, classname, bases, attrs)


@dataclass_transform(kw_only_default=True)
class Model(metaclass=ModelMeta):
    """Base class for models.

    To create custom model, you simply need to create subclass of this type and
    declare fields via annotations.
    """

    def __init__(self, **kwargs):
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
        return f"{self.__class__.__qualname__}({", ".join(items)})"

    def __setattr__(self, name: str, value: Any):
        if value is Undefined:
            return super().__setattr__(name, value)
        field = self.__class__.__fields__[name]
        parser = self.__class__.__config__.parser_provider.provide_parser(field.type)
        value = parser(value, Loc(name))
        if isinstance(value, Invalid):
            raise ParsingError(value.errors)
        super().__setattr__(name, parser(value, Loc(name)))

    def __eq__(self, value: object) -> bool:
        for name in self.__class__.__fields__:
            if getattr(self, name) != getattr(value, name):
                return False
        return True

    def __ne__(self, value: object) -> bool:
        return not self.__eq__(value)

    def validate(self):
        errors = []
        for name, field_info in self.__class__.__fields__.items():
            value = getattr(self, name)
            if value is Undefined:
                if field_info.is_required():
                    errors.append(ErrorFactory.required_missing(Loc(name)))
        if errors:
            raise ValidationError(self, tuple(errors))
