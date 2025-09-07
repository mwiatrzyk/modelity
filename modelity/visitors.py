"""Built-in implementations of the :class:`modelity.interface.IModelVisitor`
interface.

.. versionadded:: 0.17.0
"""

import collections
from numbers import Number
from typing import Any, Callable, Mapping, Sequence, Set, Union, cast

from modelity import _utils
from modelity.error import Error, ErrorFactory
from modelity.interface import IModelVisitor, ISupportsValidate
from modelity.loc import Loc
from modelity.model import Field, Model, run_model_postvalidators, run_model_prevalidators, run_field_validators
from modelity.unset import UnsetType

__all__ = export = _utils.ExportList()  # type: ignore


@export
class DefaultDumpVisitor(IModelVisitor):
    """Default visitor for serializing models into JSON-compatible dicts.

    :param out:
        The output dict to be updated.
    """

    def __init__(self, out: dict):
        self._out = out
        self._stack = collections.deque[Any]()

    def visit_model_begin(self, loc: Loc, value: Any):
        self._stack.append(dict())

    def visit_model_end(self, loc: Loc, value: Any):
        top = self._stack.pop()
        if len(self._stack) == 0:
            self._out.update(top)
        else:
            self._add(loc, top)

    def visit_mapping_begin(self, loc: Loc, value: Mapping):
        self._stack.append(dict())

    def visit_mapping_end(self, loc: Loc, value: Mapping):
        self._add(loc, self._stack.pop())

    def visit_sequence_begin(self, loc: Loc, value: Sequence):
        self._stack.append([])

    def visit_sequence_end(self, loc: Loc, value: Sequence):
        self._add(loc, self._stack.pop())

    def visit_set_begin(self, loc: Loc, value: Set):
        self._stack.append([])

    def visit_set_end(self, loc: Loc, value: Set):
        self._add(loc, self._stack.pop())

    def visit_supports_validate_begin(self, loc: Loc, value: Any):
        pass

    def visit_supports_validate_end(self, loc: Loc, value: Any):
        pass

    def visit_string(self, loc: Loc, value: str):
        self._add(loc, value)

    def visit_number(self, loc: Loc, value: Number):
        self._add(loc, value)

    def visit_bool(self, loc: Loc, value: bool):
        self._add(loc, value)

    def visit_none(self, loc: Loc, value: None):
        self._add(loc, value)

    def visit_any(self, loc: Loc, value: Any):
        if isinstance(value, str):
            return self._add(loc, value)
        if isinstance(value, (Set, Sequence)):
            return self._add(loc, list(value))
        return self._add(loc, value)

    def visit_unset(self, loc: Loc, value: UnsetType):
        self._add(loc, value)

    def _add(self, loc: Loc, value: Any):
        top: Union[dict, list] = self._stack[-1]
        if isinstance(top, dict):
            top[loc.last] = value
        else:
            top.append(value)


@export
class DefaultValidateVisitor(IModelVisitor):
    """Default visitor for model validation.

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
        self._stack = collections.deque[Any]()

    def visit_model_begin(self, loc: Loc, value: Model):
        self._stack.append(value)
        return run_model_prevalidators(value.__class__, value, self._root, self._ctx, self._errors, loc)

    def visit_model_end(self, loc: Loc, value: Model):
        run_model_postvalidators(value.__class__, value, self._root, self._ctx, self._errors, loc)
        self._stack.pop()

    def visit_mapping_begin(self, loc: Loc, value: Mapping):
        self._push_field(loc)

    def visit_mapping_end(self, loc: Loc, value: Mapping):
        self._pop_field()

    def visit_sequence_begin(self, loc: Loc, value: Sequence):
        self._push_field(loc)

    def visit_sequence_end(self, loc: Loc, value: Sequence):
        self._pop_field()

    def visit_set_begin(self, loc: Loc, value: Set):
        self._push_field(loc)

    def visit_set_end(self, loc: Loc, value: Set):
        self._pop_field()

    def visit_supports_validate_begin(self, loc: Loc, value: Any):
        pass

    def visit_supports_validate_end(self, loc: Loc, value: Any):
        _, field = self._get_current_model_and_field(loc)
        if isinstance(field.descriptor, ISupportsValidate):
            field.descriptor.validate(self._errors, loc, value)

    def visit_string(self, loc: Loc, value: str):
        self._validate_field(loc, value)

    def visit_number(self, loc: Loc, value: Number):
        self._validate_field(loc, value)

    def visit_bool(self, loc: Loc, value: bool):
        self._validate_field(loc, value)

    def visit_unset(self, loc: Loc, value: UnsetType):
        model: Model = self._stack[-1]
        field = model.__class__.__model_fields__[loc.last]
        if not field.optional:
            self._errors.append(ErrorFactory.required_missing(loc))

    def visit_none(self, loc: Loc, value: None):
        pass

    def visit_any(self, loc: Loc, value: Any):
        self._validate_field(loc, value)

    def _push_field(self, loc: Loc):
        top = self._stack[-1]
        if isinstance(top, Model):
            self._stack.append(top.__class__.__model_fields__[loc.last])

    def _pop_field(self):
        self._stack.pop()

    def _get_current_model_and_field(self, loc: Loc) -> tuple[Model, Field]:
        top = self._stack[-1]
        if isinstance(top, Model):
            return cast(Model, top), top.__class__.__model_fields__[loc.last]
        return cast(Model, self._stack[-2]), cast(Field, top)

    def _validate_field(self, loc: Loc, value: Any):
        model, _ = self._get_current_model_and_field(loc)
        run_field_validators(model.__class__, model, self._root, self._ctx, self._errors, loc, value)


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

        def proxy(loc, value):
            if value is not self._constant:
                return target(loc, value)

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

        def proxy(loc, value):
            if self._exclude_if(loc, value):
                return
            return target(loc, value)

        target = getattr(self._target, name)
        return proxy
