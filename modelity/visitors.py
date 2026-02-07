"""Built-in implementations of the :class:`modelity.interface.IModelVisitor`
interface.

.. versionadded:: 0.17.0
"""

import base64
import collections
import datetime
import enum
import functools
from typing import Any, Callable, Iterator, Literal, Mapping, MutableSequence, Optional, Sequence, Set, cast

from modelity import _utils
from modelity._internal import hooks as _int_hooks
from modelity.error import Error, ErrorFactory
from modelity.interface import IField, IModel, IModelVisitor, IValidatableTypeDescriptor
from modelity.loc import Loc
from modelity.model import Model
from modelity.unset import Unset, UnsetType

__all__ = export = _utils.ExportList()  # type: ignore


@export
class EmptyVisitor:
    """A visitor that simply implements
    :class:`modelity.interface.IModelVisitor` interface with methods doing
    nothing.

    It is meant to be used as a base for other visitors, especially ones that
    do not need to overload all methods.
    """

    def __getattr__(self, _):

        def func(*args, **kwargs):
            pass

        return func


@export
class DumpVisitor(EmptyVisitor):
    """Visitor that dumps model to dict without type narrowing or any kind of
    value formatting.

    It basically produces same structure as the model has, but based on Python
    collection types (dicts, lists, tuples and sets) instead of Modelity
    built-in ones.

    .. important::
        This visitor assumes that use of its API is done by
        :meth:`modelity.model.Model.accept` method that keeps the right order
        of method calling. It may not work correctly if used manually.

    .. versionadded:: 0.31.0
    """

    def __init__(self, out: dict):
        self._out = out
        self._stack: list[DumpVisitor._StackItem] = []
        self._model_depth = 0

    def visit_model_begin(self, loc: Loc, value: IModel):
        if self._model_depth == 0:
            self._push_dict(self._out)
        else:
            self._push_dict({})
        self._model_depth += 1

    def visit_model_end(self, loc: Loc, value: IModel):
        self._model_depth -= 1
        if self._model_depth > 0:
            self._pop_and_add(loc)

    def visit_mapping_begin(self, loc: Loc, value: Mapping):
        self._push_dict({})

    def visit_mapping_end(self, loc: Loc, value: Mapping):
        self._pop_and_add(loc)

    def visit_sequence_begin(self, loc: Loc, value: Sequence):
        self._push_list([])

    def visit_sequence_end(self, loc: Loc, value: Sequence):
        obj = self._pop()
        if not isinstance(value, MutableSequence):
            obj = tuple(obj)
        self._add(loc, obj)

    def visit_set_begin(self, loc: Loc, value: Set):
        self._push_set(set())

    def visit_set_end(self, loc: Loc, value: Set):
        self._pop_and_add(loc)

    def visit_scalar(self, loc: Loc, value: Any):
        self._add(loc, value)

    def visit_any(self, loc: Loc, value: Any):
        self._add(loc, value)

    def visit_unset(self, loc: Loc, value: UnsetType):
        self._add(loc, value)

    def visit_none(self, loc: Loc, value: None):
        self._add(loc, value)

    def _add(self, loc: Loc, value: Any):
        _, add = self._stack[-1]
        add(loc, value)

    def _pop(self) -> Any:
        return self._stack.pop()[0]

    def _pop_and_add(self, loc: Loc):
        current_top = self._pop()
        self._add(loc, current_top)

    _AddFunc = Callable[[Loc, Any], None]

    _StackItem = tuple[Any, _AddFunc]

    def _push_dict(self, obj: dict):
        self._stack.append((obj, functools.partial(self._add_dict, obj)))

    def _push_list(self, obj: list):
        self._stack.append((obj, functools.partial(self._add_list, obj)))

    def _push_set(self, obj: set):
        self._stack.append((obj, functools.partial(self._add_set, obj)))

    @staticmethod
    def _add_dict(obj: dict, loc: Loc, value: Any):
        obj[loc.last] = value

    @staticmethod
    def _add_list(obj: list, loc: Loc, value: Any):
        obj.append(value)

    @staticmethod
    def _add_set(obj: set, loc: Loc, value: Any):
        obj.add(value)


@export
class JsonDumpVisitorProxy:
    """Proxy visitor that narrows down value types to closest JSON-compatible
    type: dict, list, str, int, float, bool or None.

    .. versionadded:: 0.31.0

    :param target:
        Target dump visitor, e.g. :class:`DumpVisitor` object.

    :param exclude_unset:
        Exclude model fields equal to :obj:`modelity.unset.Unset` object.

    :param exclude_none:
        Exclude model fields equal to :obj:`None`.

        This does not affect ``None`` values used in nested containers, only
        model fields, typed with e.g. ``Optional[T]``, are affected.

    :param bytes_format:
        The format used to encode :class:`bytes` objects.

        Supports either encoding name (f.e. ``utf-8`` or ``ascii``) or one of
        predefined encodings (f.e. ``base64``).

    :param datetime_format:
        The format to use to encode :class:`datetime.datetime` objects.

        Following placeholders are supported:

        * **YYYY** for 4-digit years
        * **MM** for 2-digit months in range [01..12]
        * **DD** for 2-digit days in range [01..31]
        * **hh** for 2-digit hours in range [00..23]
        * **mm** for 2-digit minutes in range [00..59]
        * **ss** for 2-digit seconds in range [00..59]
        * **ffffff** for 6-digit microseconds in range [000000..999999]
        * **ZZZZ** for timezone

    :param date_format:
        The format to use to encode :class:`datetime.date` objects.

        Following placeholders are supported:

        * **YYYY** for 4-digit years
        * **MM** for 2-digit months in range [01..12]
        * **DD** for 2-digit days in range [01..31]

    :param default_converter:
        The default converter to use if there is no type-specific converter
        found.

        This defaults to :class:`str` type's constructor, therefore all
        non-JSON types will by default be converted to :class:`str`.
    """

    _FormatterFunc = Callable[[Any], Any]

    def __init__(
        self,
        target: IModelVisitor,
        /,
        exclude_unset: bool = False,
        exclude_none: bool = False,
        bytes_format: str | Literal["base64"] = "utf-8",
        datetime_format: str = "YYYY-MM-DDThh:mm:ss.ffffffZZZZ",
        date_format: str = "YYYY-MM-DD",
        default_converter: Optional[Callable[[Loc, Any], Any]] = None,
    ):
        self._target = target
        self._exclude_unset = exclude_unset
        self._exclude_none = exclude_none
        self._bytes_format = bytes_format
        if bytes_format == "base64":
            bytes_formatter = self._format_bytes_as_base64_str
        else:
            bytes_formatter = self._format_bytes_as_str
        self._datetime_format = _utils.compile_datetime_format(datetime_format)
        self._date_format = _utils.compile_date_format(date_format)
        self._default_converter = default_converter or (lambda loc, value: str(value))
        self._stack: list = []
        self._formatters: dict[type, JsonDumpVisitorProxy._FormatterFunc] = {
            datetime.datetime: self._format_datetime,
            datetime.date: self._format_date,
            bytes: bytes_formatter,
            str: self._unchanged,
            int: self._unchanged,
            float: self._unchanged,
            bool: self._unchanged,
        }

    def __getattr__(self, name):
        return getattr(self._target, name)

    def visit_set_begin(self, loc: Loc, value: Set):
        list_value = list(value)
        self._stack.append(list_value)
        return self._target.visit_sequence_begin(loc, list_value)

    def visit_set_end(self, loc: Loc, value: Set):
        list_value = self._stack.pop()
        return self._target.visit_sequence_end(loc, list_value)

    def visit_sequence_begin(self, loc: Loc, value: Sequence):
        list_value = list(value)
        self._stack.append(list_value)
        return self._target.visit_sequence_begin(loc, list_value)

    def visit_sequence_end(self, loc: Loc, value: Sequence):
        list_value = self._stack.pop()
        return self._target.visit_sequence_end(loc, list_value)

    def visit_scalar(self, loc: Loc, value: Any):
        value_type = type(value)
        formatter = self._formatters.get(value_type)
        if formatter is not None:
            self._target.visit_scalar(loc, formatter(value))
        elif isinstance(value, enum.Enum):
            self.visit_any(loc, value.value)
        else:
            self._target.visit_scalar(loc, self._default_converter(loc, value))

    def visit_any(self, loc: Loc, value: Any):
        if isinstance(value, Set):
            self._visit_any_sequence(loc, sorted(value, key=lambda x: repr(x)))
        elif _utils.is_neither_str_nor_bytes_sequence(value):
            self._visit_any_sequence(loc, list(value))
        elif isinstance(value, Mapping):
            self._visit_any_mapping(loc, value)
        else:
            return self.visit_scalar(loc, value)

    def visit_unset(self, loc: Loc, value: UnsetType):
        if not self._exclude_unset:
            self._target.visit_unset(loc, value)

    def visit_none(self, loc: Loc, value: None):
        if not self._exclude_none:
            self._target.visit_none(loc, value)

    def _visit_any_sequence(self, loc: Loc, value: Sequence):
        if self._target.visit_sequence_begin(loc, value) is not True:
            for i, el in enumerate(value):
                self.visit_any(loc + Loc(i), el)
            self._target.visit_sequence_end(loc, value)

    def _visit_any_mapping(self, loc: Loc, value: Mapping):
        if self._target.visit_mapping_begin(loc, value) is not True:
            for k, v in value.items():
                self.visit_any(loc + Loc(k), v)
            self._target.visit_mapping_end(loc, value)

    def _format_datetime(self, value: datetime.datetime) -> str:
        return value.strftime(self._datetime_format)

    def _format_date(self, value: datetime.date) -> str:
        return value.strftime(self._date_format)

    def _format_bytes_as_str(self, value: bytes) -> str:
        return value.decode(self._bytes_format)

    def _format_bytes_as_base64_str(self, value: bytes) -> str:
        return base64.b64encode(value).decode()

    def _unchanged(self, value: Any) -> Any:
        return value


@export
class ValidationVisitor(EmptyVisitor):
    """Visitor that performs model validation.

    .. versionchanged:: 0.31.0
        The class was renamed: **DefaultValidationVisitor** -> **ValidationVisitor**

    :param root:
        The root model.

    :param errors:
        The list of errors.

        Will be populated with validation errors (if any).

    :param ctx:
        User-defined validation context.

        It is shared across all validation hooks and can be used as a source of
        external data needed during validation but not directly available in
        the model.
    """

    def __init__(self, root: Model, errors: list[Error], ctx: Any = None):
        self._root = root
        self._errors = errors
        self._ctx = ctx
        self._memo: dict[Loc, dict] = {}
        self._location_validators_stack = collections.deque()  # type: ignore
        self._model_stack = collections.deque()  # type: ignore

    def visit_model_begin(self, loc: Loc, value: Model):
        model_type = value.__class__
        location_validators = _int_hooks.collect_location_validator_hooks(model_type)
        self._memo[loc] = {"has_location_validators": bool(location_validators)}
        if location_validators:
            self._push_location_validators(value, location_validators)
        self._push_model(value)
        return self._run_model_prevalidators(loc, value)

    def visit_model_end(self, loc: Loc, value: Model):
        if len(loc) >= 1:
            self._run_location_validators(loc, value)
        self._run_model_postvalidators(loc, value)
        self._pop_model()
        memo = self._memo.pop(loc)
        if memo["has_location_validators"]:
            self._pop_location_validators()

    def visit_model_field_begin(self, loc: Loc, value: Any, field: IField):
        if value is Unset:
            if field.is_required():
                self._errors.append(ErrorFactory.required_missing(loc))
            elif not field.is_unsettable():
                self._errors.append(ErrorFactory.unset_not_allowed(loc, field.typ))
            return True  # Skip other validators

    def visit_model_field_end(self, loc: Loc, value: Any, field: IField):
        if value is not Unset:
            self._run_field_validators(loc, value)
            if isinstance(field.descriptor, IValidatableTypeDescriptor):
                field.descriptor.validate(self._errors, loc, value)

    def visit_mapping_end(self, loc: Loc, value: Mapping):
        self._run_location_validators(loc, value)

    def visit_sequence_end(self, loc: Loc, value: Sequence):
        self._run_location_validators(loc, value)

    def visit_set_end(self, loc: Loc, value: Set):
        self._run_location_validators(loc, value)

    def visit_none(self, loc: Loc, value: None):
        self._run_location_validators(loc, value)

    def visit_scalar(self, loc: Loc, value: Any):
        self._run_location_validators(loc, value)

    def visit_any(self, loc: Loc, value: Any):
        self._run_location_validators(loc, value)

    def _push_location_validators(self, model: Model, location_validators: dict[Loc, list[_int_hooks.ILocationHook]]):
        self._location_validators_stack.append((model, location_validators))

    def _pop_location_validators(self):
        self._location_validators_stack.pop()

    def _iter_location_validators(self) -> Iterator[tuple[Model, dict[Loc, list[_int_hooks.ILocationHook]]]]:
        for item in self._location_validators_stack:
            yield item

    def _push_model(self, model: Model):
        self._model_stack.append(model)

    def _pop_model(self):
        self._model_stack.pop()

    def _current_model(self) -> Model:
        return self._model_stack[-1]

    def _run_model_prevalidators(self, loc: Loc, value: Model):
        model_type = value.__class__
        for hook in _int_hooks.collect_model_hooks(model_type, "model_prevalidator"):
            if hook(model_type, value, self._root, self._ctx, self._errors, loc) is True:
                return True
        return None

    def _run_model_postvalidators(self, loc: Loc, value: Model):
        model_type = value.__class__
        for hook in _int_hooks.collect_model_hooks(model_type, "model_postvalidator"):
            hook(model_type, value, self._root, self._ctx, self._errors, loc)

    def _run_field_validators(self, loc: Loc, value: Any):
        model = self._current_model()
        model_type = model.__class__
        for hook in _int_hooks.collect_field_hooks(model_type, "field_validator", cast(str, loc[-1])):
            hook(model_type, model, self._root, self._ctx, self._errors, loc, value)

    def _run_location_validators(self, loc: Loc, value: Any):
        for hook_model, hook_set in self._iter_location_validators():
            for pattern, hooks in hook_set.items():
                if loc.suffix_match(pattern):
                    for hook in hooks:
                        hook(hook_model.__class__, hook_model, self._root, self._ctx, self._errors, loc, value)


@export
class ModelFieldPruningVisitorProxy:
    """Visitor proxy that skips model fields if provided exclude function
    returns ``True``.

    .. important::
        This proxy only skips model fields and does not affect container
        elements in any way.

    :param target:
        The wrapped model visitor.

    :param exclude_if:
        The exclusion function.

        Takes ``(loc, value)`` as arguments and must return ``True`` to skip
        the matched model field or ``False`` to leave it.
    """

    def __init__(self, target: IModelVisitor, /, exclude_if: Callable[[Loc, Any], bool]):
        self._target = target
        self._exclude_if = exclude_if

    def __getattr__(self, name):
        return getattr(self._target, name)

    def visit_model_field_begin(self, loc: Loc, value: Any, field: IField) -> Optional[bool]:
        if self._exclude_if(loc, value):
            return True
        return self._target.visit_model_field_begin(loc, value, field)
