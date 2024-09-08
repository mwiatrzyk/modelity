import collections.abc
from typing import Any

from modelity.exc import ParsingError
from modelity.invalid import Invalid
from modelity.parsing.interface import IParser


class MutableMappingProxy(collections.abc.MutableMapping):

    def __init__(self, target: dict, loc: tuple, key_parser: IParser, value_parser: IParser):
        self._target = target
        self._loc = loc
        self._key_parser = key_parser
        self._value_parser = value_parser

    def __repr__(self):
        return repr(self._target)

    def __eq__(self, other: object) -> bool:
        return self._target == other

    def __delitem__(self, key: Any):
        del self._target[key]

    def __getitem__(self, key: Any) -> Any:
        return self._target[key]

    def __iter__(self) -> collections.abc.Iterator:
        return iter(self._target)

    def __len__(self) -> int:
        return len(self._target)

    def __setitem__(self, key: Any, value: Any) -> None:
        key = self._key_parser(key, self._loc)
        value = self._value_parser(value, self._loc)
        if isinstance(key, Invalid):
            raise ParsingError(key.errors)
        if isinstance(value, Invalid):
            raise ParsingError(value.errors)
        self._target[key] = value


class MutableSequenceProxy(collections.abc.MutableSequence):

    def __init__(self, target: list, loc: tuple, item_parser: IParser):
        self._loc = loc
        self._target = target
        self._item_parser = item_parser

    def __eq__(self, value: object) -> bool:
        return self._target == value

    def __repr__(self):
        return repr(self._target)

    def __delitem__(self, index: int):
        del self._target[index]

    def __getitem__(self, index: int):
        return self._target[index]

    def __setitem__(self, index: int, value: Any):
        value = self._item_parser(value, self._loc)
        if isinstance(value, Invalid):
            raise ParsingError(value.errors)
        self._target[index] = value

    def __len__(self):
        return len(self._target)

    def insert(self, index: int, value: Any) -> None:
        value = self._item_parser(value, self._loc)
        if isinstance(value, Invalid):
            raise ParsingError(value.errors)
        return self._target.insert(index, value)


class MutableSetProxy(collections.abc.MutableSet):

    def __init__(self, target: set, loc: tuple, item_parser: IParser):
        self._target = target
        self._loc = loc
        self._item_parser = item_parser

    def __repr__(self) -> str:
        return repr(self._target)

    def __contains__(self, x: object) -> bool:
        return x in self._target

    def __iter__(self) -> collections.abc.Iterator:
        return iter(self._target)

    def __len__(self) -> int:
        return len(self._target)

    def add(self, value: Any):
        value = self._item_parser(value, self._loc)
        if isinstance(value, Invalid):
            raise ParsingError(value.errors)
        self._target.add(value)

    def discard(self, value: Any):
        self._target.discard(value)
