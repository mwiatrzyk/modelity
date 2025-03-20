import collections
import functools

from numbers import Number
from typing import Any, Callable, Mapping, Sequence, Set, TextIO

from modelity.interface import IModel, IModelVisitor
from modelity.loc import Loc
from modelity.unset import UnsetType


class ExcludingVisitorProxy:
    """Proxy visitor that forwards calls to given target visitor only if given
    location and/or value is not excluded.

    To check if location and/or value should be excluded, user defined function
    is used.

    :param target:
        Target visitor.

    :param exclude_if:
        User-defined callable that should return ``True`` if location and/or
        value should be excluded, or ``False`` otherwise.
    """

    def __init__(self, target: IModelVisitor, exclude_if: Callable[[Loc, Any], bool]):
        self._target = target
        self._should_exclude = exclude_if

    def __getattr__(self, name):
        target_func = getattr(self._target, name)
        return functools.partial(self.__call_visit, target_func)

    def __call_visit(self, target_func: Callable[[Loc, Any], None], loc: Loc, value: Any):
        if not self._should_exclude(loc, value):
            target_func(loc, value)


class DumpModelVisitor:
    """Visitor that dumps model to a dict.

    :param out:
        The dictionary to update with dumped model.

        Should be initially empty.
    """

    def __init__(self, out: dict):
        self._stack = collections.deque([self._ObjectAdapter(out)])

    def visit_object_begin(self, loc: Loc, value: Any):
        data = {}
        self._stack.append(data)
        self._stack.append(self._ObjectAdapter(data))

    def visit_object_end(self, loc: Loc, value: Any):
        self._stack.pop()
        data = self._stack.pop()
        self._stack[-1].add(loc, data)

    def visit_array_begin(self, loc: Loc, value: Any):
        data = []
        self._stack.append(data)
        self._stack.append(self._ArrayAdapter(data))

    def visit_array_end(self, loc: Loc, value: Any):
        self._stack.pop()
        data = self._stack.pop()
        self._stack[-1].add(loc, data)

    def visit_string(self, loc: Loc, value: str):
        self._add_value(loc, value)

    def visit_number(self, loc: Loc, value: Number):
        self._add_value(loc, value)

    def visit_bool(self, loc: Loc, value: bool):
        self._add_value(loc, value)

    def visit_any(self, loc: Loc, value: Any):
        self._add_value(loc, value)

    def visit_none(self, loc: Loc, value: None):
        self._add_value(loc, value)

    def visit_unset(self, loc: Loc, value: UnsetType):
        self._add_value(loc, value)

    def _add_value(self, loc: Loc, value: Any):
        self._stack[-1].add(loc, value)

    class _ObjectAdapter:

        def __init__(self, out: dict):
            self._out = out

        def add(self, loc: Loc, value: Any):
            self._out[loc.last] = value

    class _ArrayAdapter:

        def __init__(self, out: list):
            self._out = out

        def add(self, loc: Loc, value: Any):
            self._out.append(value)


class DumpJsonModelVisitor:

    def __init__(self, buf: TextIO):
        self._stack = collections.deque([self._ObjectAdapter(buf)])

    def visit_number(self, loc: Loc, value: Number):
        self._add_value(loc, value)

    def visit_any(self, loc: Loc, value: Any):
        self._add_value(loc, value)

    def _add_value(self, loc: Loc, value: Any):
        self._stack[-1].add(loc, value)

    class _BaseAdapter:

        def __init__(self, buf: TextIO):
            self.buf = buf

    class _ObjectAdapter(_BaseAdapter):

        def add(self, loc: Loc, value: Any):
            self.buf.write(f'"{loc.last}":{value!r}')

    class _ArrayAdapter(_BaseAdapter):

        def add(self, loc: Loc, value: Any):
            pass
