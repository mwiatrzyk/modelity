from typing import AbstractSet, Any, Iterable, Iterator, Mapping, MutableMapping, MutableSequence, MutableSet

from typing_extensions import Self

from modelity.base import TypeHandler
from modelity.error import Error
from modelity.exc import ParsingError
from modelity.loc import Loc
from modelity.unset import Unset


class MutableMappingProxy(MutableMapping):
    """Proxy class for mutable mappings that adds parsing logic on modifications.

    :param typ:
        The type of the original mapping.

    :param target:
        The wrapped target mapping.

    :param key_type_handler:
        The type handler used to parse keys.

    :param value_type_handler:
        The type handler used to parse values.
    """

    __slots__ = ("_typ", "_target", "_key_type_handler", "_value_type_handler")

    def __init__(
        self, typ: type[Mapping], target: MutableMapping, key_type_handler: TypeHandler, value_type_handler: TypeHandler
    ):
        self._typ = typ
        self._target = target
        self._key_type_handler = key_type_handler
        self._value_type_handler = value_type_handler

    def __repr__(self) -> str:
        return repr(self._target)

    def __eq__(self, other):
        return self._target == other

    def __delitem__(self, key: Any) -> None:
        del self._target[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        errors: list[Error] = []
        self._set_item(self._target, key, value, errors)
        if errors:
            raise ParsingError(self._typ, tuple(errors))

    def _set_item(self, out: MutableMapping, key, value, errors: list[Error]):
        key = self._key_type_handler.parse(errors, Loc.irrelevant(), key)
        if key is Unset:
            return
        value = self._value_type_handler.parse(errors, Loc(key), value)
        if value is Unset:
            return
        out[key] = value

    def __getitem__(self, key: Any) -> Any:
        return self._target[key]

    def __iter__(self) -> Iterator:
        return iter(self._target)

    def __len__(self) -> int:
        return len(self._target)

    def setdefault(self, key: Any, default: Any = None, /) -> Any:
        if key not in self:
            self[key] = default
        return self[key]

    def update(self, m=None, /, **kwargs):
        errors: list[Error] = []
        if m is None:
            for k, v in kwargs.items():
                self._set_item(self._target, k, v, errors)
        else:
            input_data = dict(m)
            input_data.update(**kwargs)
            for k, v in input_data.items():
                self._set_item(self._target, k, v, errors)
        if errors:
            raise ParsingError(self._typ, tuple(errors))


class MutableSequenceProxy(MutableSequence):
    """Proxy class for mutable sequences (e.g. lists) that adds parsing logic on modifications.

    :param typ:
        The type of the original sequence.

    :param target:
        The target mutable sequence to wrap.

    :param item_type_handler:
        The type handler used to parse items.
    """

    __slots__ = ["_typ", "_target", "_item_type_handler"]

    def __init__(self, typ: type[MutableSequence], target: MutableSequence, item_type_handler: TypeHandler, /):
        self._typ = typ
        self._target = target
        self._item_type_handler = item_type_handler

    def __repr__(self) -> str:
        return repr(self._target)

    def __eq__(self, other):
        return self._target == other

    def __delitem__(self, index):
        del self._target[index]

    def __getitem__(self, index):
        return self._target[index]

    def __setitem__(self, index, value):
        self._target[index] = self._parse_item(index, value)

    def __len__(self):
        return len(self._target)

    def insert(self, index, value):
        self._target.insert(index, self._parse_item(index, value))

    def extend(self, values: Iterable) -> None:
        errors: list[Error] = []
        parse = self._item_type_handler.parse
        parsed_values = [parse(errors, Loc(i), item) for i, item in enumerate(values)]
        if errors:
            raise ParsingError(self._typ, tuple(errors))
        self._target.extend(parsed_values)

    def _parse_item(self, index, value):
        errors = []
        result = self._item_type_handler.parse(errors, Loc(index), value)
        if result is Unset:
            raise ParsingError(self._typ, tuple(errors))
        return result


class MutableSetProxy(MutableSet):
    """Proxy class for mutable sets that adds parsing logic on modifications.

    :param typ:
        The type of the original set.

    :param target:
        The wrapped target set object.

    :param item_type_handler:
        The type handler to use to parse set items.
    """

    __slots__ = ["_typ", "_target", "_item_type_handler"]

    def __init__(self, typ: type[MutableSet], target: MutableSet, item_type_handler: TypeHandler):
        self._typ = typ
        self._target = target
        self._item_type_handler = item_type_handler

    def __repr__(self):
        return repr(self._target)

    def __contains__(self, x: object) -> bool:
        return self._target.__contains__(x)

    def __iter__(self):
        return iter(self._target)

    def __len__(self) -> int:
        return len(self._target)

    def __ior__(self, other: AbstractSet) -> Self:
        self._target |= self._parse_many(other)
        return self

    def __or__(self, other: AbstractSet[Any]) -> AbstractSet[Any]:
        return self._target | other

    def __and__(self, other: AbstractSet[Any]) -> AbstractSet:
        return self._target & other

    def __sub__(self, other: AbstractSet[Any]) -> AbstractSet:
        return self._target - other

    def __xor__(self, other: AbstractSet[Any]) -> AbstractSet[Any]:
        return self._target ^ other

    def _parse_many(self, value: AbstractSet) -> set:
        errors: list[Error] = []
        parse = self._item_type_handler.parse
        loc = Loc.irrelevant()
        parsed_value = set(parse(errors, loc, x) for x in value)
        if len(errors) > 0:
            raise ParsingError(value.__class__, tuple(errors))
        return parsed_value

    def add(self, value):
        errors = []
        parsed_value = self._item_type_handler.parse(errors, Loc.irrelevant(), value)
        if len(errors) > 0:
            raise ParsingError(self._typ, tuple(errors))
        self._target.add(parsed_value)

    def discard(self, value):
        self._target.discard(value)
