from typing import Any, Optional, Tuple, Type, get_args, get_origin

from typing_extensions import dataclass_transform

from modelity.unset import Unset


@dataclass_transform(kw_only_default=True)
class Field:
    """Dataclass with user-editable field properties.

    Instances of this class can be used to annotate field declaration in a
    model to provide details like default value or more.

    Example:

    .. testcode::

        class Dummy(Model):
            foo: int = Field(default=123)
    """

    __slots__ = ("default", "optional")

    #: Field's default value.
    default: Any

    #: Flag telling if this field is optional.
    #:
    #: Normally, you should use :class:`typing.Optional` to indicate that the
    #: field is optional. However, field declared like that allow ``None`` to be
    #: explicitly set. If you need to indicate that the field is optional, but
    #: to also disallow ``None`` as the valid value, then this is the option
    #: you'll need.
    optional: bool

    def __init__(self, default: Any = Unset, optional: bool = False):
        self.default = default
        self.optional = optional

    def compute_default(self) -> Any:
        """Compute default value for this field."""
        return self.default


class BoundField(Field):
    """Object containing field metadata.

    Objects of this type are automatically created from type annotations, but
    can also be created explicitly to override field defaults (see :meth:`field`
    for details).
    """

    __slots__ = ("name", "type", "_type_origin", "_type_args")

    #: Field's name.
    name: str

    #: Field's full type.
    type: Type

    def __init__(self, name: str, type: Type, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.type = type
        self._type_origin = get_origin(type)
        self._type_args = get_args(type)

    def __repr__(self) -> str:
        return f"<{self.__module__}.{self.__class__.__qualname__}(name={self.name!r}, type={self.type!r}, default={self.default!r})>"

    def __eq__(self, value: object) -> bool:
        if type(value) is not BoundField:
            return False
        return self.name == value.name and self.type == value.type and self.default == value.default

    def __ne__(self, value: object) -> bool:
        return not self.__eq__(value)

    def is_optional(self):
        """Check if this field is optional."""
        return self.optional or self.default is not Unset or type(None) in self.type_args

    def is_required(self):
        """Check if this field is required.

        This is simply a negation of :meth:`is_optional` method.
        """
        return not self.is_optional()

    @property
    def type_origin(self) -> Optional[Type]:
        """Field's type origin.

        For example, if field's type is ``List[str]``, then this will be set to
        ``list``.
        """
        return self._type_origin

    @property
    def type_args(self) -> Tuple:
        """Field's type args.

        For example, if field's type is ``Dict[str, int]``, then this will be
        set to ``(str, int)``.
        """
        return self._type_args
