from typing import Any, MutableSequence, Sequence, cast, get_args, get_origin

from modelity import _utils
from modelity._parsing.type_proxies import MutableSequenceProxy
from modelity.base import ModelVisitor, TypeHandler, TypeHandlerFactory
from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType, is_unset


def _ensure_sequence(typ: type[Sequence], errors: list[Error], loc: Loc, value: Any) -> Sequence | UnsetType:
    if _utils.is_neither_str_nor_bytes_sequence(value):
        return value
    errors.append(ErrorFactory.invalid_type(loc, value, [typ], [Sequence], [str, bytes]))
    return Unset


class BaseMutableSequenceTypeHandler(TypeHandler):
    typ: type[MutableSequence]

    def __init__(self, typ: type[MutableSequence]):
        self.typ = typ
        origin = get_origin(typ)
        is_mutable_sequence = (
            issubclass(typ, MutableSequence) if origin is None else issubclass(origin, MutableSequence)
        )
        if not is_mutable_sequence:
            raise TypeError(f"unsupported type; got {typ!r}, expected MutableSequence")


class AnyMutableSequenceHandler(BaseMutableSequenceTypeHandler):

    def __init__(self, typ: type[MutableSequence]):
        super().__init__(typ)
        args = get_args(typ)
        if args and args != (Any,):
            raise TypeError(f"unsupported type; got {typ!r}, expected one of: MutableSequence, MutableSequence[Any]")

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        result = _ensure_sequence(self.typ, errors, loc, value)
        if is_unset(result):
            return Unset
        return list(result)

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visit_any = visitor.visit_any
        if visitor.visit_sequence_begin(loc, value) is not True:
            for i, item in enumerate(value):
                visit_any(loc + Loc(i), item)
            visitor.visit_sequence_end(loc, value)


class TypedMutableSequenceHandler(BaseMutableSequenceTypeHandler):

    def __init__(self, typ: type[MutableSequence], type_handler_factory: TypeHandlerFactory, /, **type_opts):
        super().__init__(typ)
        args = get_args(typ)
        if len(args) != 1:
            raise TypeError(f"unsupported type; got {typ!r}, expected MutableSequence[T]")
        self._item_type_handler = type_handler_factory(args[0], **type_opts)

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        result = _ensure_sequence(self.typ, errors, loc, value)
        if is_unset(result):
            return Unset
        item_type_handler = self._item_type_handler
        parse_item = item_type_handler.parse
        result = [parse_item(errors, loc + Loc(i), x) for i, x in enumerate(result)]
        if len(errors) > 0:
            return Unset
        return MutableSequenceProxy(self.typ, result, item_type_handler)

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        item_accept = self._item_type_handler.accept
        if visitor.visit_sequence_begin(loc, value) is not True:
            for p, item in enumerate(value):
                item_accept(visitor, loc + Loc(p), item)
            visitor.visit_sequence_end(loc, value)


def create_mutable_sequence_type_handler(
    typ: type[MutableSequence], type_handler_factory: TypeHandlerFactory, /, **type_opts
) -> TypeHandler:
    args = get_args(typ)
    if not args or args == (Any,):
        return AnyMutableSequenceHandler(typ)
    return TypedMutableSequenceHandler(typ, type_handler_factory, **type_opts)


class BaseSequenceTypeHandler(TypeHandler):
    typ: type[Sequence]

    def __init__(self, typ: type[Sequence]):
        self.typ = typ
        origin = get_origin(typ)
        is_sequence = issubclass(typ, Sequence) if origin is None else issubclass(origin, Sequence)
        if not is_sequence:
            raise TypeError(f"unsupported type; got {typ!r}, expected Sequence")


class AnySequenceTypeHandler(BaseSequenceTypeHandler):

    def __init__(self, typ: type[Sequence]):
        super().__init__(typ)
        args = get_args(typ)
        if args and args != (Any, ...) and args != (Any,):
            raise TypeError(f"unsupported type; got {typ!r}, expected one of: Sequence, Sequence[Any], tuple[Any, ...]")

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        result = _ensure_sequence(self.typ, errors, loc, value)
        if is_unset(result):
            return result
        return tuple(result)

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        if visitor.visit_sequence_begin(loc, value) is not True:
            for i, item in enumerate(value):
                visitor.visit_any(loc + Loc(i), item)
            visitor.visit_sequence_end(loc, value)


class TypedSequenceTypeHandler(BaseSequenceTypeHandler):

    def __init__(self, typ: type[Sequence], type_handler_factory: TypeHandlerFactory, /, **type_opts):
        super().__init__(typ)
        args = get_args(typ)
        if not args or (len(args) == 2 and args[-1] is not Ellipsis) or len(args) > 2:
            raise TypeError(f"unsupported type; got {typ!r}, expected one of: Sequence[T], tuple[T, ...]")
        assert len(args) >= 1
        self._item_type_handler = type_handler_factory(args[0], **type_opts)

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        result = _ensure_sequence(self.typ, errors, loc, value)
        if is_unset(result):
            return result
        parse_item = self._item_type_handler.parse
        result = tuple(parse_item(errors, loc + Loc(pos), x) for pos, x in enumerate(result))
        if len(errors) > 0:
            return Unset
        return result

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        accept_item = self._item_type_handler.accept
        if visitor.visit_sequence_begin(loc, value) is not True:
            for i, elem in enumerate(value):
                accept_item(visitor, loc + Loc(i), elem)
            visitor.visit_sequence_end(loc, value)


class FixedTupleTypeHandler(TypeHandler):

    def __init__(self, typ: type[Sequence], type_handler_factory: TypeHandlerFactory, /, **type_opts):
        origin = get_origin(typ)
        args = get_args(typ)
        if origin is None or origin is not tuple or (len(args) == 2 and args[-1] is Ellipsis):
            raise TypeError(f"unsupported type; got {typ!r}, expected tuple[A, B, ..., Z]")
        self._typ = typ
        self._inner_types = args
        self._inner_type_handlers = [type_handler_factory(x, **type_opts) for x in args]

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        result = _ensure_sequence(self._typ, errors, loc, value)
        if is_unset(result):
            return result
        result = cast(tuple, result)
        if len(result) != len(self._inner_type_handlers):
            errors.append(ErrorFactory.invalid_tuple_length(loc, tuple(result), self._inner_types))
            return Unset
        result = tuple(
            desc.parse(errors, loc + Loc(i), item)
            for desc, i, item in zip(self._inner_type_handlers, range(len(self._inner_type_handlers)), result)
        )
        if len(errors) > 0:
            return Unset
        return result

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        if visitor.visit_sequence_begin(loc, value) is not True:
            for i, elem, handler in zip(range(len(self._inner_type_handlers)), value, self._inner_type_handlers):
                handler.accept(visitor, loc + Loc(i), elem)
            visitor.visit_sequence_end(loc, value)


def create_sequence_type_handler(
    typ: type[Sequence], type_handler_factory: TypeHandlerFactory, /, **type_opts
) -> TypeHandler:
    args = get_args(typ)
    if not args or args == (Any,) or args == (Any, ...):
        return AnySequenceTypeHandler(typ)
    if len(args) == 1 or (len(args) == 2 and args[-1] is Ellipsis):
        return TypedSequenceTypeHandler(typ, type_handler_factory, **type_opts)
    return FixedTupleTypeHandler(typ, type_handler_factory, **type_opts)
