import collections

from typing import Any, Mapping, Sequence, Set

from modelity.interface import IModel
from modelity.loc import Loc
from modelity.unset import UnsetType


class DumpVisitor:
    """Default visitor for dumping :class:`modelity.model.Model` object into a
    Python dict.

    It is used internally by the helper function :func:`modelity.model.dump`.

    :param out:
        The dictionary to update with dumped model.

        Should be initially empty.

    :param exclude_unset:
        Exclude :class:`modelity.unset.UnsetType` values from resulting dict.

    :param exclude_none:
        Exclude ``None`` values from resulting dict.
    """

    def __init__(self, out: dict, exclude_unset: bool=False, exclude_none: bool=False):

        def noop(loc, value):
            pass

        self._stack = collections.deque([self._DictAdapter(out)])
        if exclude_unset:
            self.visit_unset = noop
        if exclude_none:
            self.visit_none = noop

    def visit_sequence_begin(self, loc: Loc, value: Sequence):
        data = []
        self._stack.append(data)
        self._stack.append(self._ListAdapter(data))

    def visit_sequence_end(self, loc: Loc, value: Sequence):
        self._stack.pop()
        data = self._stack.pop()
        self._stack[-1].add(loc, data)

    def visit_mapping_begin(self, loc: Loc, value: Mapping):
        data = {}
        self._stack.append(data)
        self._stack.append(self._DictAdapter(data))

    def visit_mapping_end(self, loc: Loc, value: Mapping):
        self._stack.pop()
        data = self._stack.pop()
        self._stack[-1].add(loc, data)

    def visit_set_begin(self, loc: Loc, value: Set):
        self.visit_sequence_begin(loc, value)

    def visit_set_end(self, loc: Loc, value: Set):
        self.visit_sequence_end(loc, value)

    def visit_model_begin(self, loc: Loc, value: IModel):
        self.visit_mapping_begin(loc, value)

    def visit_model_end(self, loc: Loc, value: IModel):
        self.visit_mapping_end(loc, value)

    def visit_scalar(self, loc: Loc, value: IModel):
        self._stack[-1].add(loc, value)

    def visit_none(self, loc: Loc, value: None):
        self._stack[-1].add(loc, value)

    def visit_unset(self, loc: Loc, value: UnsetType):
        self._stack[-1].add(loc, value)

    class _DictAdapter:

        def __init__(self, out: dict):
            self._out = out

        def add(self, loc: Loc, value: Any):
            self._out[loc.last] = value

    class _ListAdapter:

        def __init__(self, out: list):
            self._out = out

        def add(self, loc: Loc, value: Any):
            self._out.append(value)
