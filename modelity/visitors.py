"""Built-in implementations of the :class:`modelity.interface.IModelVisitor`
interface.

.. versionadded:: 0.17.0
"""

import collections
from numbers import Number
from typing import Any, Callable, Mapping, Optional, Sequence, Set, Union

from modelity import _utils
from modelity.error import Error, ErrorFactory
from modelity.interface import IModelVisitor, IValidatableTypeDescriptor
from modelity.loc import Loc
from modelity.model import Field, Model, run_model_postvalidators, run_model_prevalidators, run_field_validators
from modelity.unset import Unset, UnsetType

__all__ = export = _utils.ExportList()  # type: ignore


@export
class EmptyVisitor(IModelVisitor):
    """A visitor that simply implements
    :class:`modelity.interface.IModelVisitor` interface with methods doing
    nothing.

    It is meant to be used as a base for other visitors, especially ones that
    do not need to overload all the methods.
    """

    def visit_model_begin(self, loc: Loc, value: Any) -> Optional[bool]:
        pass

    def visit_model_end(self, loc: Loc, value: Any):
        pass

    def visit_model_field_begin(self, loc: Loc, value: Any, field: Any) -> Optional[bool]:
        pass

    def visit_model_field_end(self, loc: Loc, value: Any, field: Any):
        pass

    def visit_mapping_begin(self, loc: Loc, value: Mapping) -> Optional[bool]:
        pass

    def visit_mapping_end(self, loc: Loc, value: Mapping):
        pass

    def visit_sequence_begin(self, loc: Loc, value: Sequence) -> Optional[bool]:
        pass

    def visit_sequence_end(self, loc: Loc, value: Sequence):
        pass

    def visit_set_begin(self, loc: Loc, value: Set) -> Optional[bool]:
        pass

    def visit_set_end(self, loc: Loc, value: Set):
        pass

    def visit_supports_validate_begin(self, loc: Loc, value: Any) -> Optional[bool]:
        pass

    def visit_supports_validate_end(self, loc: Loc, value: Any):
        pass

    def visit_string(self, loc: Loc, value: str):
        pass

    def visit_number(self, loc: Loc, value: Number):
        pass

    def visit_bool(self, loc: Loc, value: bool):
        pass

    def visit_none(self, loc: Loc, value: None):
        pass

    def visit_any(self, loc: Loc, value: Any):
        pass

    def visit_unset(self, loc: Loc, value: UnsetType):
        pass


@export
class DefaultDumpVisitor(EmptyVisitor):
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
class DefaultValidateVisitor(EmptyVisitor):
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
        self._model_stack = collections.deque[Model]()
        self._field_stack = collections.deque[Field]()

    def visit_model_begin(self, loc: Loc, value: Model):
        self._push_model(value)
        return run_model_prevalidators(value.__class__, value, self._root, self._ctx, self._errors, loc)

    def visit_model_end(self, loc: Loc, value: Model):
        run_model_postvalidators(value.__class__, value, self._root, self._ctx, self._errors, loc)
        self._pop_model()

    def visit_model_field_begin(self, loc: Loc, value: Any, field: Field):
        if value is Unset and not field.optional:
            self._errors.append(ErrorFactory.required_missing(loc))
            return True  # Skip other validators if required field is missing
        self._push_field(field)

    def visit_model_field_end(self, loc: Loc, value: Any, field: Any):
        if value is not Unset:
            self._validate_field(loc, value)
        self._pop_field()

    def visit_supports_validate_end(self, loc: Loc, value: Any):
        field = self._current_field()
        if isinstance(field.descriptor, IValidatableTypeDescriptor):
            field.descriptor.validate(self._errors, loc, value)

    def _push_model(self, model: Model):
        self._model_stack.append(model)

    def _pop_model(self):
        self._model_stack.pop()

    def _push_field(self, field: Field):
        self._field_stack.append(field)

    def _pop_field(self):
        self._field_stack.pop()

    def _current_model(self):
        return self._model_stack[-1]

    def _current_field(self):
        return self._field_stack[-1]

    def _validate_field(self, loc: Loc, value: Any):
        model = self._current_model()
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
