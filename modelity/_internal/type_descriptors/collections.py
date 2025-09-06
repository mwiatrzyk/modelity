from collections.abc import Set
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
    cast,
    get_args,
)

from modelity._internal.registry import TypeDescriptorFactoryRegistry
from modelity._utils import is_neither_str_nor_bytes_sequence
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError
from modelity.interface import IModelVisitor, ITypeDescriptor, ITypeDescriptorFactory
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType, is_unset

registry = TypeDescriptorFactoryRegistry()


@registry.type_descriptor_factory(dict)
def make_dict_type_descriptor(typ, make_type_descriptor, type_opts) -> ITypeDescriptor:

    class MutableMappingProxy(MutableMapping):
        __slots__ = ["_data"]

        def __init__(self, initial_data: dict):
            self._data = initial_data

        def __repr__(self):
            return repr(self._data)

        def __delitem__(self, key) -> None:
            del self._data[key]

        def __setitem__(self, key, value) -> None:
            errors: list[Error] = []
            self.__setitem(self._data, key, value, errors)
            if errors:
                raise ParsingError(typ, tuple(errors))

        def __setitem(self, out: dict, key, value, errors: list[Error]):
            key = key_type_descriptor.parse(errors, Loc.irrelevant(), key)
            if key is Unset:
                return
            value = value_type_descriptor.parse(errors, Loc(key), value)
            if value is Unset:
                return
            out[key] = value

        def __getitem__(self, key):
            return self._data[key]

        def __iter__(self) -> Iterator:
            return iter(self._data)

        def __len__(self) -> int:
            return len(self._data)

    def ensure_mapping(errors: list[Error], loc: Loc, value: Any) -> Union[Mapping, UnsetType]:
        if isinstance(value, Mapping):
            return value
        errors.append(ErrorFactory.dict_parsing_error(loc, value))
        return Unset

    def parse_typed(errors: list[Error], loc: Loc, value: Any) -> Union[Mapping, UnsetType]:
        result = ensure_mapping(errors, loc, value)
        if result is Unset:
            return result
        result = dict(
            (
                key_type_descriptor.parse(errors, loc + Loc.irrelevant(), k),
                value_type_descriptor.parse(errors, loc + Loc(k), v),
            )
            for k, v in cast(Mapping, result).items()
        )
        if len(errors) > 0:
            return Unset
        return result

    class AnyDictTypeDescriptor(ITypeDescriptor[Mapping]):
        def parse(self, errors, loc, value):
            result = ensure_mapping(errors, loc, value)
            if result is Unset:
                return result
            return dict(result)  # type: ignore

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Mapping):
            if visitor.visit_mapping_begin(loc, value) is not True:
                for k, v in value.items():
                    visitor.visit_any(loc + Loc(k), v)
                visitor.visit_mapping_end(loc, value)

    class TypedDictTypeDescriptor(ITypeDescriptor[Mapping]):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = parse_typed(errors, loc, value)
            if len(errors) > 0:
                return Unset
            return MutableMappingProxy(cast(dict, result))

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Mapping):
            if visitor.visit_mapping_begin(loc, value) is not True:
                for k, v in value.items():
                    value_type_descriptor.accept(visitor, loc + Loc(k), v)
                visitor.visit_mapping_end(loc, value)

    args = get_args(typ)
    if not args:
        return AnyDictTypeDescriptor()
    key_type_descriptor = cast(ITypeDescriptor, make_type_descriptor(args[0], type_opts))
    value_type_descriptor = cast(ITypeDescriptor, make_type_descriptor(args[1], type_opts))
    return TypedDictTypeDescriptor()


@registry.type_descriptor_factory(list)
def make_list_type_descriptor(typ, make_type_descriptor, type_opts) -> ITypeDescriptor:

    class MutableSequenceProxy(MutableSequence):
        __slots__ = ["_data"]

        def __init__(self, initial_value: list):
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
            self._data[index] = self.__parse_item(index, value)

        def __len__(self):
            return len(self._data)

        def insert(self, index, value):
            self._data.insert(index, self.__parse_item(index, value))

        def __parse_item(self, index, value):
            errors = []
            result = type_descriptor.parse(errors, Loc(index), value)
            if result is not Unset:
                return result
            raise ParsingError(typ, tuple(errors))

    def ensure_sequence(errors: list[Error], loc: Loc, value: Any) -> Union[Sequence, UnsetType]:
        if is_neither_str_nor_bytes_sequence(value):
            return value
        errors.append(ErrorFactory.list_parsing_error(loc, value))
        return Unset

    def parse_typed(errors: list[Error], loc: Loc, value: Any) -> Union[Sequence, UnsetType]:
        result = ensure_sequence(errors, loc, value)
        if result is Unset:
            return Unset
        result = cast(Sequence, result)
        result = list(type_descriptor.parse(errors, loc + Loc(i), x) for i, x in enumerate(result))
        if len(errors) > 0:
            return Unset
        return result

    class AnyListDescriptor(ITypeDescriptor[list]):

        def parse(self, errors, loc, value):
            result = ensure_sequence(errors, loc, value)
            if is_unset(result):
                return result
            return list(cast(Sequence, result))

        def accept(self, visitor: IModelVisitor, loc: Loc, value: list):
            if visitor.visit_sequence_begin(loc, value) is not True:
                for i, item in enumerate(value):
                    visitor.visit_any(loc + Loc(i), item)
                visitor.visit_sequence_end(loc, value)

    class TypedListDescriptor(ITypeDescriptor[list]):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = parse_typed(errors, loc, value)
            if len(errors) > 0:
                return Unset
            result = cast(list, result)
            return MutableSequenceProxy(result)

        def accept(self, visitor: IModelVisitor, loc: Loc, value: list):
            if visitor.visit_sequence_begin(loc, value) is not True:
                for p, item in enumerate(value):
                    type_descriptor.accept(visitor, loc + Loc(p), item)
                visitor.visit_sequence_end(loc, value)

    args = get_args(typ)
    if len(args) == 0:
        return AnyListDescriptor()
    type_descriptor: ITypeDescriptor = make_type_descriptor(args[0], type_opts)
    return TypedListDescriptor()


@registry.type_descriptor_factory(set)
def make_set_type_descriptor(typ, make_type_descriptor: ITypeDescriptorFactory, type_opts: dict) -> ITypeDescriptor:

    class MutableSetProxy(MutableSet):
        __slots__ = ["_data"]

        def __init__(self, initial_value: set):
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
            self._data.add(type_descriptor.parse(errors, Loc.irrelevant(), value))
            if len(errors) > 0:
                raise ParsingError(typ, tuple(errors))

        def discard(self, value):
            self._data.discard(value)

    def ensure_sequence(errors: list[Error], loc: Loc, value: Any) -> Union[Sequence, UnsetType]:
        if is_neither_str_nor_bytes_sequence(value) or isinstance(value, Set):
            return value
        errors.append(ErrorFactory.set_parsing_error(loc, value))
        return Unset

    def parse_any_set(errors: list[Error], loc: Loc, value: Any):
        result = ensure_sequence(errors, loc, value)
        if result is Unset:
            return Unset
        try:
            return set(cast(Sequence, result))
        except TypeError:
            errors.append(ErrorFactory.set_parsing_error(loc, value))
            return Unset

    class AnySetDescriptor(ITypeDescriptor[set]):
        def parse(self, errors, loc, value):
            return parse_any_set(errors, loc, value)

        def accept(self, visitor: IModelVisitor, loc: Loc, value: set):
            item_loc = loc + Loc.irrelevant()
            if visitor.visit_set_begin(loc, value) is not True:
                for item in value:
                    visitor.visit_any(item_loc, item)
                visitor.visit_set_end(loc, value)

    class TypedSetDescriptor(ITypeDescriptor[set]):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            seq = ensure_sequence(errors, loc, value)
            if seq is Unset:
                return seq
            result = set(type_descriptor.parse(errors, loc + Loc.irrelevant(), x) for x in cast(Sequence, seq))
            if len(errors) > 0:
                return Unset
            return MutableSetProxy(result)

        def accept(self, visitor: IModelVisitor, loc: Loc, value: set):
            item_loc = loc + Loc.irrelevant()
            if visitor.visit_set_begin(loc, value) is not True:
                for item in value:
                    type_descriptor.accept(visitor, item_loc, item)
                visitor.visit_set_end(loc, value)

    args = get_args(typ)
    if not args:
        return AnySetDescriptor()
    if not isinstance(args[0], type) or not issubclass(args[0], Hashable):
        raise TypeError("'T' must be hashable type to be used with 'set[T]' generic type")
    type_descriptor: ITypeDescriptor = make_type_descriptor(args[0], type_opts)
    return TypedSetDescriptor()


@registry.type_descriptor_factory(tuple)
def make_tuple_type_descriptor(typ, make_type_descriptor: ITypeDescriptorFactory, type_opts: dict) -> ITypeDescriptor:

    def ensure_sequence(errors: list[Error], loc: Loc, value: Any) -> Union[Sequence, UnsetType]:
        if is_neither_str_nor_bytes_sequence(value):
            return value
        errors.append(ErrorFactory.tuple_parsing_error(loc, value))
        return Unset

    class AnyTupleDescriptor(ITypeDescriptor[tuple]):
        def parse(self, errors, loc, value):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return result
            return tuple(result)

        def accept(self, visitor: IModelVisitor, loc: Loc, value: tuple):
            if visitor.visit_sequence_begin(loc, value) is not True:
                for i, item in enumerate(value):
                    visitor.visit_any(loc + Loc(i), item)
                visitor.visit_sequence_end(loc, value)

    class AnyLengthTypedTupleDescriptor(ITypeDescriptor[tuple]):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            seq = ensure_sequence(errors, loc, value)
            if seq is Unset:
                return Unset
            result = tuple(
                type_descriptor.parse(errors, loc + Loc(pos), x) for pos, x in enumerate(cast(Sequence, seq))
            )
            if len(errors) > 0:
                return Unset
            return result

        def accept(self, visitor: IModelVisitor, loc: Loc, value: tuple):
            if visitor.visit_sequence_begin(loc, value) is not True:
                for i, elem in enumerate(value):
                    type_descriptor.accept(visitor, loc + Loc(i), elem)
                visitor.visit_sequence_end(loc, value)

    class FixedLengthTypedTupleDescriptor(ITypeDescriptor[tuple]):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return Unset
            result = cast(tuple, result)
            if len(result) != num_type_descriptors:
                errors.append(ErrorFactory.invalid_tuple_format(loc, result, args))
                return Unset
            result = tuple(
                desc.parse(errors, loc + Loc(i), item)
                for desc, i, item in zip(type_descriptors, range(len(type_descriptors)), result)
            )
            if len(errors) > 0:
                return Unset
            return result

        def accept(self, visitor: IModelVisitor, loc: Loc, value: tuple):
            if visitor.visit_sequence_begin(loc, value) is not True:
                for i, elem, desc in zip(range(len(type_descriptors)), value, type_descriptors):
                    desc.accept(visitor, loc + Loc(i), elem)
                visitor.visit_sequence_end(loc, value)

    args = get_args(typ)
    if not args:
        return AnyTupleDescriptor()
    if args[-1] is Ellipsis:
        type_descriptor: ITypeDescriptor = make_type_descriptor(args[0], type_opts)
        return AnyLengthTypedTupleDescriptor()
    type_descriptors: tuple[ITypeDescriptor, ...] = tuple(make_type_descriptor(x, type_opts) for x in args)
    num_type_descriptors = len(type_descriptors)
    return FixedLengthTypedTupleDescriptor()
