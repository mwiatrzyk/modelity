"""Built-in implementations of the :class:`modelity.interface.IModelVisitor`
interface.

.. versionadded:: 0.17.0
"""

import collections
import datetime
import enum
from typing import Any, Callable, Iterator, Mapping, Sequence, Set, cast

from modelity import _utils
from modelity._internal import hooks as _int_hooks
from modelity.error import Error, ErrorFactory
from modelity.interface import IField, IModelVisitor, IValidatableTypeDescriptor
from modelity.loc import Loc
from modelity.model import Field, Model
from modelity.unset import Unset, UnsetType

__all__ = export = _utils.ExportList()  # type: ignore


@export
class EmptyVisitor:
    """A visitor that simply implements
    :class:`modelity.interface.IModelVisitor` interface with methods doing
    nothing.

    It is meant to be used as a base for other visitors, especially ones that
    do not need to overload all the methods.
    """

    def __getattr__(self, _):

        def func(*args, **kwargs):
            pass

        return func


@export
class DumpVisitor(EmptyVisitor):
    """Default visitor for serializing models into JSON-compatible dicts.

    .. versionchanged:: 0.31.0
        The class was renamed: **DefaultDumpVisitor** -> **DumpVisitor**

    :param out:
        The output dict.

    :param datetime_format:
        The format to use for :class:`datetime.datetime` objects.

        .. versionadded:: 0.31.0

    :param date_format:
        The format to use for :class:`datetime.date` objects.

        .. versionadded:: 0.31.0
    """

    def __init__(
        self,
        out: dict,
        datetime_format: str = "YYYY-MM-DDThh:mm:ss.ffffffZZZZ",
        date_format: str = "YYYY-MM-DD",
    ):
        self._out = out
        self._datetime_format = _utils.compile_datetime_format(datetime_format)
        self._date_format = _utils.compile_datetime_format(date_format)
        self._stack: list[tuple] = []

    def visit_model_begin(self, loc: Loc, value: Any):
        self._push_dict({} if self._stack else self._out)

    def visit_model_end(self, loc: Loc, value: Any):
        obj, _ = self._stack.pop()
        if self._stack:
            self._add(loc, obj)

    def visit_mapping_begin(self, loc: Loc, value: Mapping):
        self._push_dict({})

    def visit_mapping_end(self, loc: Loc, value: Mapping):
        self._pop_and_add(loc)

    def visit_sequence_begin(self, loc: Loc, value: Sequence):
        self._push_array([])

    def visit_sequence_end(self, loc: Loc, value: Sequence):
        self._pop_and_add(loc)

    def visit_set_begin(self, loc: Loc, value: Set):
        self._push_array([])

    def visit_set_end(self, loc: Loc, value: Set):
        self._pop_and_add(loc)

    def visit_none(self, loc: Loc, value: None):
        self._add(loc, value)

    def visit_unset(self, loc: Loc, value: UnsetType):
        self._add(loc, value)

    def visit_scalar(self, loc: Loc, value: Any):
        if isinstance(value, (int, float)):
            return self._add(loc, value)
        if isinstance(value, bytes):
            return self._add(loc, value.decode("utf-8"))  # TODO: add option to customize this
        if isinstance(value, enum.Enum):
            return self._add(loc, value.value)
        if isinstance(value, datetime.datetime):
            return self._add(loc, value.strftime(self._datetime_format))
        if isinstance(value, datetime.date):
            return self._add(loc, value.strftime(self._date_format))
        return self._add(loc, str(value))

    def visit_any(self, loc: Loc, value: Any):
        if isinstance(value, (str, bytes)):
            self.visit_scalar(loc, value)
        elif isinstance(value, Sequence):
            if self.visit_sequence_begin(loc, value) is not True:
                for i, el in enumerate(value):
                    self.visit_any(loc + Loc(i), el)
                self.visit_sequence_end(loc, value)
        else:
            self.visit_scalar(loc, value)

    def _add(self, loc: Loc, value: Any):
        self._stack[-1][-1].add(loc, value)

    def _push_dict(self, obj: dict):
        self._stack.append((obj, self._DictAdapter(obj)))

    def _push_array(self, obj: list):
        self._stack.append((obj, self._ArrayAdapter(obj)))

    def _pop_and_add(self, loc: Loc):
        self._add(loc, self._stack.pop()[0])

    class _DictAdapter:

        def __init__(self, obj: dict):
            self._obj = obj

        def add(self, loc: Loc, value: Any):
            self._obj[loc.last] = value

    class _ArrayAdapter:

        def __init__(self, obj: list):
            self._obj = obj

        def add(self, loc: Loc, value: Any):
            self._obj.append(value)


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
        self._field_stack = collections.deque()  # type: ignore

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
        self._push_field(field)

    def visit_model_field_end(self, loc: Loc, value: Any, field: IField):
        if value is not Unset:
            self._run_field_validators(loc, value)
            if isinstance(field.descriptor, IValidatableTypeDescriptor):
                field.descriptor.validate(self._errors, loc, value)
        self._pop_field()

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

    def _push_field(self, field: IField):
        self._field_stack.append(field)

    def _pop_field(self):
        self._field_stack.pop()

    def _current_model(self) -> Model:
        return self._model_stack[-1]

    def _current_field(self) -> IField:
        return self._field_stack[-1]

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
class ConstantExcludingModelVisitorProxy:
    """Visitor proxy that skips values that are equal to constant provided.

    :param target:
        The wrapped model visitor.

    :param constant:
        The constant to exclude.
    """

    def __init__(self, target: IModelVisitor, constant: Any):
        self._target = target
        self._constant = constant

    def __getattr__(self, name):

        def proxy(loc, value, *args):
            if value is not self._constant:
                return target(loc, value, *args)

        target = getattr(self._target, name)
        return proxy


@export
class ConditionalExcludingModelVisitorProxy:
    """Visitor proxy that skips values if provided exclude function returns
    ``True``.

    :param target:
        The wrapped model visitor.

    :param exclude_if:
        The exclusion function.

        Takes ``(loc, value)`` as arguments and must return ``True`` to exclude
        object or ``False`` otherwise.
    """

    def __init__(self, target: IModelVisitor, exclude_if: Callable[[Loc, Any], bool]):
        self._target = target
        self._exclude_if = exclude_if

    def __getattr__(self, name):

        def proxy(loc, value, *args):
            if self._exclude_if(loc, value):
                return
            return target(loc, value, *args)

        target = getattr(self._target, name)
        return proxy
