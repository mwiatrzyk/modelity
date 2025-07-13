import collections
from numbers import Number
from typing import Any, Callable, Mapping, Sequence, Set, Union, cast

from modelity.error import Error, ErrorFactory
from modelity.interface import IModel, IModelVisitor
from modelity.loc import Loc
from modelity.model import BoundField, Model
from modelity.unset import Unset, UnsetType
from modelity.decorators import _get_model_prevalidation_hooks, _get_model_postvalidation_hooks, _get_field_validation_hooks


class DefaultDumpVisitor(IModelVisitor):

    def __init__(self, out: dict):
        self._out = out
        self._stack = collections.deque()

    def visit_model_begin(self, loc: Loc, value: IModel):
        self._stack.append(dict())

    def visit_model_end(self, loc: Loc, value: IModel):
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
            top.append(value)  # There are no more options, so let it fail if something is changed here


class DefaultValidateVisitor(IModelVisitor):

    def __init__(self, root: IModel, errors: list[Error], ctx: Any=None):
        self._root = root
        self._errors = errors
        self._ctx = ctx
        self._stack = collections.deque()

    def visit_model_begin(self, loc: Loc, value: IModel):
        self._stack.append(value)
        model_cls = value.__class__
        for model_prevalidator in _get_model_prevalidation_hooks(model_cls):
            model_prevalidator(model_cls, value, self._root, self._ctx, self._errors, loc)  # type: ignore

    def visit_model_end(self, loc: Loc, value: IModel):
        model_cls = value.__class__
        for model_postvalidator in _get_model_postvalidation_hooks(model_cls):
            model_postvalidator(model_cls, value, self._root, self._ctx, self._errors, loc)  # type: ignore
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

    def visit_string(self, loc: Loc, value: str):
        self._validate_field(loc, value)

    def visit_number(self, loc: Loc, value: Number):
        self._validate_field(loc, value)

    def visit_bool(self, loc: Loc, value: bool):
        self._validate_field(loc, value)

    def visit_unset(self, loc: Loc, value: UnsetType):
        model: IModel = self._stack[-1]
        field = model.__model_fields__[loc.last]
        if not field.optional:
            self._errors.append(ErrorFactory.required_missing(loc))

    def visit_none(self, loc: Loc, value: None):
        pass

    def visit_any(self, loc: Loc, value: Any):
        self._validate_field(loc, value)

    def _push_field(self, loc: Loc):
        top = self._stack[-1]
        if isinstance(top, Model):
            self._stack.append(top.__model_fields__[loc.last])

    def _pop_field(self):
        self._stack.pop()

    def _validate_field(self, loc: Loc, value: Any):
        top = self._stack[-1]
        if isinstance(top, Model):
            model = cast(IModel, top)
            field = top.__model_fields__[loc.last]
        else:
            model = cast(IModel, self._stack[-2])
            field = cast(BoundField, top)
        model_cls = model.__class__
        for field_validator in _get_field_validation_hooks(model_cls, field.name):
            field_validator(model_cls, model, self._root, self._ctx, self._errors, loc, value)  # type: ignore
        field.descriptor.validate(self._errors, loc, value)


class ConstantExcludingModelVisitorProxy:

    def __init__(self, target: IModelVisitor, constant: Any):
        self._target = target
        self._constant = constant

    def __getattr__(self, name):

        def proxy(loc, value):
            if value is not self._constant:
                return target(loc, value)

        target = getattr(self._target, name)
        return proxy


class ConditionalExcludingModelVisitorProxy:

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
