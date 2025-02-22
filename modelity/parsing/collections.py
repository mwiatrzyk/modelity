from typing import (
    Any,
    Hashable,
    Iterable,
    Iterator,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Union,
    get_args,
)

from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.interface import IParser
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType


def make_dict_parser(typ, **opts):
    """Make parser for the dict type.

    :param typ:
        Dict type to create parser for.
    """

    class MutableMappingProxy(MutableMapping):
        __slots__ = ["_root_loc", "_data"]

        def __init__(self, root_loc: Loc, initial_data: dict):
            self._root_loc = root_loc
            self._data = initial_data

        def __repr__(self):
            return repr(self._data)

        def __delitem__(self, key) -> None:
            del self._data[key]

        def __setitem__(self, key, value) -> None:
            errors = []
            key = key_parser(errors, self._root_loc, key)
            if key is Unset:
                raise ParsingError(tuple(errors))
            value = value_parser(errors, self._root_loc + Loc(key), value)
            if value is Unset:
                raise ParsingError(tuple(errors))
            self._data[key] = value

        def __getitem__(self, key):
            return self._data[key]

        def __iter__(self) -> Iterator:
            return iter(self._data)

        def __len__(self) -> int:
            return len(self._data)

    def parse_dict(errors: list[Error], loc: Loc, value: Any) -> Union[dict, UnsetType]:
        try:
            return dict(value)
        except (ValueError, TypeError):
            errors.append(ErrorFactory.mapping_required(loc, value))
            return Unset

    def parse_typed_dict(errors: list[Error], loc: Loc, value: Any):
        result = parse_dict(errors, loc, value)
        if result is Unset:
            return result
        result = dict((key_parser(errors, loc, k), value_parser(errors, loc + Loc(k), v)) for k, v in result.items())
        if len(errors) > 0:
            return Unset
        return MutableMappingProxy(loc, result)

    from modelity.parsing.main import make_parser

    args = get_args(typ)
    if not args:
        return parse_dict
    key_parser, value_parser = make_parser(args[0], **opts), make_parser(args[1], **opts)
    return parse_typed_dict


def make_list_parser(typ, **opts):
    """Make parser for given list type.

    Handles both plain lists and typed ones

    :param typ:
        List type to make parser for.
    """

    class MutableSequenceProxy(MutableSequence):
        __slots__ = ["_loc", "_data"]

        def __init__(self, loc: Loc, initial_value: list):
            self._loc = loc
            self._data = initial_value

        def __repr__(self) -> str:
            return repr(self._data)

        def __eq__(self, other):
            return self._data == other

        def __delitem__(self, index):
            del self._data[index]

        def __getitem__(self, index):
            return self._data[index]

        def __setitem__(self, index, value):
            self._data[index] = self._parse_item(index, value)

        def __len__(self):
            return len(self._data)

        def insert(self, index, value):
            self._data.insert(index, self._parse_item(index, value))

        def _parse_item(self, index, value):
            errors = []
            result = item_parser(errors, self._loc + Loc(index), value)
            if result is not Unset:
                return result
            raise ParsingError(tuple(errors))

    def parse_any_list(errors: list[Error], loc: Loc, value: Any) -> Union[list, UnsetType]:
        try:
            return list(value)
        except TypeError:
            errors.append(ErrorFactory.iterable_required(loc, value))
            return Unset

    def parse_typed_list(errors: list[Error], loc: Loc, value: Any):
        result = parse_any_list(errors, loc, value)
        if result is Unset:
            return Unset
        result = list(item_parser(errors, loc + Loc(i), x) for i, x in enumerate(result))
        if len(errors) > 0:
            return Unset
        return MutableSequenceProxy(loc, result)

    from modelity.parsing.main import make_parser

    args = get_args(typ)
    if len(args) == 0:
        return parse_any_list
    item_parser = make_parser(args[0], **opts)
    return parse_typed_list


def make_set_parser(typ, **opts):
    """Make parser for set type."""

    class MutableSetProxy(MutableSet):
        __slots__ = ["_loc", "_data"]

        def __init__(self, loc: Loc, initial_value: set):
            self._loc = loc
            self._data = initial_value

        def __repr__(self):
            return repr(self._data)

        def __contains__(self, x: object) -> bool:
            return self._data.__contains__(x)

        def __iter__(self):
            return iter(self._data)

        def __len__(self) -> int:
            return len(self._data)

        def add(self, value):
            errors = []
            self._data.add(item_parser(errors, self._loc, value))
            if len(errors) > 0:
                raise ParsingError(tuple(errors))

        def discard(self, value):
            self._data.discard(value)

    def ensure_iterable(errors: list[Error], loc: Loc, value: Any) -> Union[Iterable, UnsetType]:
        if isinstance(value, Iterable):
            return value
        errors.append(ErrorFactory.iterable_required(loc, value))
        return Unset

    def parse_any_set(errors: list[Error], loc: Loc, value: Any):
        result = ensure_iterable(errors, loc, value)
        if result is Unset:
            return Unset
        try:
            return set(value)
        except TypeError as e:
            errors.append(ErrorFactory.hashable_required(loc, value))
            return Unset

    def parse_typed_set(errors: list[Error], loc: Loc, value: Any):
        result = ensure_iterable(errors, loc, value)
        if result is Unset:
            return result
        result = set(item_parser(errors, loc, x) for x in result)
        if len(errors) > 0:
            return Unset
        return MutableSetProxy(loc, result)

    from modelity.parsing.main import make_parser

    args = get_args(typ)
    if not args:
        return parse_any_set
    if not isinstance(args[0], type) or not issubclass(args[0], Hashable):
        raise TypeError("'T' must be hashable type to be used with 'set[T]' generic type")
    item_parser = make_parser(args[0], **opts)
    return parse_typed_set


def make_tuple_parser(typ, **opts) -> IParser:
    """Make parser for given tuple type.

    Returned parser can parse any kind of tuple, both typed and untyped.

    :param typ:
        Tuple type to create parser for.
    """

    def parse_any_tuple(errors: list[Error], loc: Loc, value: Any) -> Union[tuple, UnsetType]:
        try:
            return tuple(value)
        except TypeError:
            errors.append(ErrorFactory.unsupported_type(loc, [Iterable], value))
            return Unset

    def parse_any_length_typed_tuple(errors: list[Error], loc: Loc, value: Any):
        result = parse_any_tuple(errors, loc, value)
        if result is Unset:
            return Unset
        result = tuple(parser(errors, loc + Loc(pos), x) for pos, x in enumerate(result))
        if len(errors) > 0:
            return Unset
        return result

    def parse_fixed_length_typed_tuple(errors: list[Error], loc: Loc, value: Any):
        result = parse_any_tuple(errors, loc, value)
        if result is Unset:
            return Unset
        if len(result) < len(parsers):
            errors.append(ErrorFactory.tuple_too_short(loc, result, len(parsers)))
            return Unset
        if len(result) > len(parsers):
            errors.append(ErrorFactory.tuple_too_long(loc, result, len(parsers)))
            return Unset
        result = tuple(
            parse(errors, loc + Loc(i), item) for parse, i, item in zip(parsers, range(len(parsers)), result)
        )
        if len(errors) > 0:
            return Unset
        return result

    from modelity.parsing.main import make_parser

    args = get_args(typ)
    if not args:
        return parse_any_tuple
    if args[-1] is Ellipsis:
        parser = make_parser(args[0], **opts)
        return parse_any_length_typed_tuple
    parsers = tuple(make_parser(x, **opts) for x in args)
    return parse_fixed_length_typed_tuple
