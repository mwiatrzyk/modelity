import collections
from numbers import Number
from typing import Any, Callable, Mapping, Sequence, Set, Union

from modelity.interface import IModel, IModelVisitor
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType


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
