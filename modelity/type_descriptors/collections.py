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
from modelity.interface import ITypeDescriptor, IModelVisitor
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType


def make_dict_type_descriptor(typ: type[dict], **opts) -> ITypeDescriptor:
    """Make type descriptor for the :class:`dict` type, both typed and untyped.

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

    class AnyDictTypeDescriptor:
        def parse(self, errors, loc, value):
            result = ensure_mapping(errors, loc, value)
            if result is Unset:
                return result
            return dict(result)

        def accept(self, loc: Loc, value: dict, visitor: IModelVisitor):
            visitor.visit_mapping_begin(loc, value)
            for k, v in value.items():
                visitor.visit_scalar(loc + Loc(k), v)
            visitor.visit_mapping_end(loc, value)

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

        def accept(self, loc: Loc, value: dict, visitor: IModelVisitor):
            visitor.visit_mapping_begin(loc, value)
            for k, v in value.items():
                value_type_descriptor.accept(loc + Loc(k), v, visitor)
            visitor.visit_mapping_end(loc, value)

    from modelity.type_descriptors.main import make_type_descriptor

    args = get_args(typ)
    if not args:
        return AnyDictTypeDescriptor()
    key_type_descriptor, value_type_descriptor = make_type_descriptor(args[0], **opts), make_type_descriptor(
        args[1], **opts
    )
    return TypedDictTypeDescriptor()


def make_list_type_descriptor(typ, **opts) -> ITypeDescriptor:
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
            result = type_descriptor.parse(errors, self._loc + Loc(index), value)
            if result is not Unset:
                return result
            raise ParsingError(tuple(errors))

    def ensure_sequence(errors: list[Error], loc: Loc, value: Any) -> Union[Sequence, UnsetType]:
        if is_neither_str_nor_bytes_sequence(value):
            return value
        errors.append(ErrorFactory.invalid_list(loc, value))
        return Unset

    class AnyListDescriptor:

        def parse(self, errors, loc, value):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return result
            return list(result)

        def accept(self, loc: Loc, value: list, visitor: IModelVisitor):
            visitor.visit_sequence_begin(loc, value)
            for i, elem in enumerate(value):
                visitor.visit_scalar(loc + Loc(i), elem)
            visitor.visit_sequence_end(loc, value)

        def validate(self, errors: list[Error], loc: Loc, value: list):
            return None

    class TypedListDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return Unset
            result = list(type_descriptor.parse(errors, loc + Loc(i), x) for i, x in enumerate(result))
            if len(errors) > 0:
                return Unset
            return MutableSequenceProxy(loc, result)

        def accept(self, loc: Loc, value: list, visitor: IModelVisitor):
            visitor.visit_sequence_begin(loc, value)
            for i, elem in enumerate(value):
                type_descriptor.accept(loc + Loc(i), elem, visitor)
            visitor.visit_sequence_end(loc, value)

    from modelity.type_descriptors.main import make_type_descriptor

    args = get_args(typ)
    if len(args) == 0:
        return AnyListDescriptor()
    type_descriptor = make_type_descriptor(args[0], **opts)
    return TypedListDescriptor()


def make_set_type_descriptor(typ, **opts) -> ITypeDescriptor:
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

    class AnySetDescriptor:
        def parse(self, errors, loc, value):
            return parse_any_set(errors, loc, value)

        def accept(self, loc: Loc, value: set, visitor: IModelVisitor):
            visitor.visit_set_begin(loc, value)
            for elem in value:
                visitor.visit_scalar(loc, elem)
            visitor.visit_set_end(loc, value)

    class TypedSetDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return result
            result = set(type_descriptor.parse(errors, loc, x) for x in result)
            if len(errors) > 0:
                return Unset
            return MutableSetProxy(loc, result)

        def accept(self, loc: Loc, value: set, visitor: IModelVisitor):
            visitor.visit_set_begin(loc, value)
            for elem in value:
                type_descriptor.accept(loc, elem, visitor)
            visitor.visit_set_end(loc, value)

    from modelity.type_descriptors.main import make_type_descriptor

    args = get_args(typ)
    if not args:
        return AnySetDescriptor()
    if not isinstance(args[0], type) or not issubclass(args[0], Hashable):
        raise TypeError("'T' must be hashable type to be used with 'set[T]' generic type")
    type_descriptor = make_type_descriptor(args[0], **opts)
    return TypedSetDescriptor()


def make_tuple_type_descriptor(typ, **opts) -> ITypeDescriptor:
    """Make parser for given tuple type.

    Returned parser can parse any kind of tuple, both typed and untyped.

    :param typ:
        Tuple type to create parser for.
    """

    def ensure_sequence(errors: list[Error], loc: Loc, value: Any) -> Union[Sequence, UnsetType]:
        if is_neither_str_nor_bytes_sequence(value):
            return value
        errors.append(ErrorFactory.invalid_tuple(loc, value))
        return Unset

    class AnyTupleDescriptor:
        def parse(self, errors, loc, value):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return result
            return tuple(result)

        def accept(self, loc: Loc, value: tuple, visitor: IModelVisitor):
            visitor.visit_sequence_begin(loc, value)
            for i, elem in enumerate(value):
                visitor.visit_scalar(loc + Loc(i), elem)
            visitor.visit_sequence_end(loc, value)

    class AnyLengthTypedTupleDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            result = ensure_sequence(errors, loc, value)
            if result is Unset:
                return Unset
            result = tuple(type_descriptor.parse(errors, loc + Loc(pos), x) for pos, x in enumerate(result))
            if len(errors) > 0:
                return Unset
            return result

        def accept(self, loc: Loc, value: tuple, visitor: IModelVisitor):
            visitor.visit_sequence_begin(loc, value)
            for i, elem in enumerate(value):
                type_descriptor.accept(loc + Loc(i), elem, visitor)
            visitor.visit_sequence_end(loc, value)

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

        def accept(self, loc: Loc, value: tuple, visitor: IModelVisitor):
            visitor.visit_sequence_begin(loc, value)
            for i, p in enumerate(zip(value, type_descriptors)):
                p[1].accept(loc + Loc(i), p[0], visitor)
            visitor.visit_sequence_end(loc, value)

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
