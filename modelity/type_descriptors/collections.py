from typing import (
    Any,
    Hashable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Union,
    get_args,
)

from modelity._utils import is_neither_str_nor_bytes_sequence
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.interface import IDumpFilter, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType


def make_dict_type_descriptor(typ: type[dict], **opts) -> ITypeDescriptor:
    """Make descriptor for :class:`dict` type.

    Following variants are supported:

    * ``dict`` (plain dict, with any keys and any values)
    * ``dict[K, V]`` (typed dict, with keys of type *K*, and values of type *V*)

    :param typ:
        The type to create parser for.

    :param `**opts`:
        The options to be passed to inner type descriptors.
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
            key = key_type_descriptor.parse(errors, self._root_loc, key)
            if key is Unset:
                raise ParsingError(tuple(errors))
            value = value_type_descriptor.parse(errors, self._root_loc + Loc(key), value)
            if value is Unset:
                raise ParsingError(tuple(errors))
            self._data[key] = value

        def __getitem__(self, key):
            return self._data[key]

        def __iter__(self) -> Iterator:
            return iter(self._data)

        def __len__(self) -> int:
            return len(self._data)

    def ensure_mapping(errors: list[Error], loc: Loc, value: Any) -> Union[Mapping, UnsetType]:
        if isinstance(value, Mapping):
            return value
        errors.append(ErrorFactory.invalid_dict(loc, value))
        return Unset

    def dump(loc: Loc, value: dict, filter: IDumpFilter) -> dict:
        result = {}
        for k, v in value.items():
            v = filter(loc, v)
            if v is not IDumpFilter.SKIP:
                result[k] = v
        return result

    class AnyDictTypeDescriptor:
        def parse(self, errors, loc, value):
            result = ensure_mapping(errors, loc, value)
            if result is Unset:
                return result
            return dict(result)

        def dump(self, loc: Loc, value: dict, filter: IDumpFilter):
            return dump(loc, value, filter)

        def validate(self, root, ctx, errors, loc, value):
            return

    class TypedDictTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = ensure_mapping(errors, loc, value)
            if result is Unset:
                return result
            result = dict(
                (key_type_descriptor.parse(errors, loc, k), value_type_descriptor.parse(errors, loc + Loc(k), v))
                for k, v in result.items()
            )
            if len(errors) > 0:
                return Unset
            return MutableMappingProxy(loc, result)

        def validate(self, root, ctx, errors, loc, value: dict):
            for k, v in value.items():
                value_type_descriptor.validate(root, ctx, errors, loc + Loc(k), v)

        def dump(self, loc: Loc, value: dict, filter: IDumpFilter):
            return dump(loc, value, lambda l, v: value_type_descriptor.dump(l, v, filter))

    from modelity.type_descriptors.main import make_type_descriptor

    args = get_args(typ)
    if not args:
        return AnyDictTypeDescriptor()
    key_type_descriptor, value_type_descriptor = make_type_descriptor(args[0], **opts), make_type_descriptor(
        args[1], **opts
    )
    return TypedDictTypeDescriptor()


def make_list_type_descriptor(typ, **opts) -> ITypeDescriptor:
    """Make descriptor for :class:`list` type.

    Following type variants are supported:

    * ``list`` (plain, untyped lists)
    * ``list[T]`` (typed list, with each item of type *T*)

    :param typ:
        The type to create descriptor for.

    :param `**opts`:
        Type options.
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
            result = type_descriptor.parse(errors, self._loc + Loc(index), value)
            if result is not Unset:
                return result
            raise ParsingError(tuple(errors))

    def ensure_sequence(errors: list[Error], loc: Loc, value: Any) -> Union[Sequence, UnsetType]:
        if is_neither_str_nor_bytes_sequence(value):
            return value
        errors.append(ErrorFactory.invalid_list(loc, value))
        return Unset

    def dump(loc: Loc, value: list, filter: IDumpFilter) -> list:
        result = []
        for i, elem in enumerate(value):
            dump_value = filter(loc + Loc(i), elem)
            if dump_value is not IDumpFilter.SKIP:
                result.append(dump_value)
        return result

    class AnyListDescriptor:

        def parse(self, errors, loc, value):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return result
            return list(result)

        def dump(self, loc: Loc, value: list, filter: IDumpFilter):
            return dump(loc, value, filter)

        def validate(self, root, ctx, errors, loc, value):
            return

    class TypedListDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return Unset
            result = list(type_descriptor.parse(errors, loc + Loc(i), x) for i, x in enumerate(result))
            if len(errors) > 0:
                return Unset
            return MutableSequenceProxy(loc, result)

        def dump(self, loc: Loc, value: list, filter: IDumpFilter):
            return dump(loc, value, lambda l, v: type_descriptor.dump(l, v, filter))

        def validate(self, root, ctx, errors, loc, value: list):
            for i, elem in enumerate(value):
                type_descriptor.validate(root, ctx, errors, loc + Loc(i), elem)

    from modelity.type_descriptors.main import make_type_descriptor

    args = get_args(typ)
    if len(args) == 0:
        return AnyListDescriptor()
    type_descriptor = make_type_descriptor(args[0], **opts)
    return TypedListDescriptor()


def make_set_type_descriptor(typ, **opts) -> ITypeDescriptor:
    """Make descriptor for :class:`set` type.

    Following type variants are supported:

    * ``set`` (untyped sets, with items of any type)
    * ``set[T]`` (typed sets, with items of type *T*)

    :param typ:
        The type to create descriptor for.

    :param `**opts`:
        Type options.
    """

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
            self._data.add(type_descriptor.parse(errors, self._loc, value))
            if len(errors) > 0:
                raise ParsingError(tuple(errors))

        def discard(self, value):
            self._data.discard(value)

    def ensure_sequence(errors: list[Error], loc: Loc, value: Any) -> Union[Sequence, UnsetType]:
        if is_neither_str_nor_bytes_sequence(value):
            return value
        errors.append(ErrorFactory.invalid_set(loc, value))
        return Unset

    def parse_any_set(errors: list[Error], loc: Loc, value: Any):
        result = ensure_sequence(errors, loc, value)
        if result is Unset:
            return Unset
        try:
            return set(result)
        except TypeError:
            errors.append(ErrorFactory.invalid_set(loc, value))
            return Unset

    def dump(loc: Loc, value: set, filter: IDumpFilter) -> list:
        result = []
        for elem in value:
            elem = filter(loc, elem)
            if elem is not IDumpFilter.SKIP:
                result.append(elem)
        return result

    class AnySetDescriptor:
        def parse(self, errors, loc, value):
            return parse_any_set(errors, loc, value)

        def dump(self, loc: Loc, value: set, filter: IDumpFilter):
            return dump(loc, value, filter)

        def validate(self, root, ctx, errors, loc, value: set):
            pass

    class TypedSetDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return result
            result = set(type_descriptor.parse(errors, loc, x) for x in result)
            if len(errors) > 0:
                return Unset
            return MutableSetProxy(loc, result)

        def dump(self, loc: Loc, value: set, filter: IDumpFilter):
            return dump(loc, value, lambda l, v: type_descriptor.dump(l, v, filter))

        def validate(self, root, ctx, errors, loc, value: set):
            pass

    from modelity.type_descriptors.main import make_type_descriptor

    args = get_args(typ)
    if not args:
        return AnySetDescriptor()
    if not isinstance(args[0], type) or not issubclass(args[0], Hashable):
        raise TypeError("'T' must be hashable type to be used with 'set[T]' generic type")
    type_descriptor = make_type_descriptor(args[0], **opts)
    return TypedSetDescriptor()


def make_tuple_type_descriptor(typ, **opts) -> ITypeDescriptor:
    """Make descriptor for :class:`tuple` type.

    Following type variants are supported:

    * ``tuple`` (untyped, unlimited size)
    * ``tuple[T, ...]`` (typed, unlimited size, with items of type *T*)
    * ``tuple[A, B, ..., Z] (typed, fixed size, with items of type *A*, *B*, ..., *Z*)

    :param typ:
        The type to create descriptor for.

    :param `**opts`:
        The options to be passed to inner type descriptors.
    """

    def ensure_sequence(errors: list[Error], loc: Loc, value: Any) -> Union[Sequence, UnsetType]:
        if is_neither_str_nor_bytes_sequence(value):
            return value
        errors.append(ErrorFactory.invalid_tuple(loc, value))
        return Unset

    def dump(loc: Loc, value: tuple, filter: IDumpFilter) -> list:
        result = []
        for i, elem in enumerate(value):
            elem = filter(loc + Loc(i), elem)
            if elem is not IDumpFilter.SKIP:
                result.append(elem)
        return result

    class AnyTupleDescriptor:
        def parse(self, errors, loc, value):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return result
            return tuple(result)

        def dump(self, loc: Loc, value: tuple, filter: IDumpFilter):
            return dump(loc, value, filter)

        def validate(self, root, ctx, errors, loc, value):
            pass

    class AnyLengthTypedTupleDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return Unset
            result = tuple(type_descriptor.parse(errors, loc + Loc(pos), x) for pos, x in enumerate(result))
            if len(errors) > 0:
                return Unset
            return result

        def dump(self, loc: Loc, value: tuple, filter: IDumpFilter):
            return dump(loc, value, lambda l, v: type_descriptor.dump(l, v, filter))

        def validate(self, root, ctx, errors, loc, value: tuple):
            for i, elem in enumerate(value):
                type_descriptor.validate(root, ctx, errors, loc + Loc(i), elem)

    class FixedLengthTypedTupleDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return Unset
            if len(result) != num_type_descriptors:
                errors.append(ErrorFactory.unsupported_tuple_format(loc, result, args))
                return Unset
            result = tuple(
                desc.parse(errors, loc + Loc(i), item)
                for desc, i, item in zip(type_descriptors, range(len(type_descriptors)), result)
            )
            if len(errors) > 0:
                return Unset
            return result

        def dump(self, loc: Loc, value: tuple, filter: IDumpFilter):
            return dump(loc, value, lambda l, v: type_descriptors[l.last].dump(l, v, filter))

        def validate(self, root, ctx, errors, loc, value: tuple):
            for i, elem, desc in zip(range(len(type_descriptors)), value, type_descriptors):
                desc.validate(root, ctx, errors, loc + Loc(i), elem)

    from modelity.type_descriptors.main import make_type_descriptor

    args = get_args(typ)
    if not args:
        return AnyTupleDescriptor()
    if args[-1] is Ellipsis:
        type_descriptor = make_type_descriptor(args[0], **opts)
        return AnyLengthTypedTupleDescriptor()
    type_descriptors = tuple(make_type_descriptor(x, **opts) for x in args)
    num_type_descriptors = len(type_descriptors)
    return FixedLengthTypedTupleDescriptor()
