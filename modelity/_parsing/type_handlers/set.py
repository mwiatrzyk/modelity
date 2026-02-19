from typing import Any, MutableSet, Sequence, Set, get_args, get_origin

from modelity import _utils
from modelity._parsing.type_proxies import MutableSetProxy
from modelity.base import ModelVisitor, TypeHandler, TypeHandlerFactory
from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType, is_unset


class BaseMutableSetTypeHandler(TypeHandler):
    typ: type[MutableSet]

    def __init__(self, typ: type[MutableSet]):
        origin = get_origin(typ)
        is_mutable_set = issubclass(typ, MutableSet) if origin is None else issubclass(origin, MutableSet)
        if not is_mutable_set:
            raise TypeError(f"unsupported type; got {typ!r}, expected MutableSet")
        self.typ = typ

    def ensure_sequence_or_set(self, errors: list[Error], loc: Loc, value: Any) -> Sequence | Set | UnsetType:
        if _utils.is_neither_str_nor_bytes_sequence(value) or isinstance(value, Set):
            return value
        errors.append(ErrorFactory.invalid_type(loc, value, [self.typ], [Set, Sequence], [str, bytes]))
        return Unset


class AnyMutableSetTypeHandler(BaseMutableSetTypeHandler):

    def __init__(self, typ: type[MutableSet]):
        super().__init__(typ)
        args = get_args(typ)
        if args and args != (Any,):
            raise TypeError(f"unsupported type; got {typ!r}, expected one of: MutableSet, MutableSet[Any]")

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        result = self.ensure_sequence_or_set(errors, loc, value)
        if is_unset(result):
            return Unset
        try:
            return set(result)
        except TypeError:
            errors.append(ErrorFactory.conversion_error(loc, value, self.typ, "some elements are unhashable"))
            return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        item_loc = loc + Loc.irrelevant()
        visit_any = visitor.visit_any
        if visitor.visit_set_begin(loc, value) is not True:
            for item in value:
                visit_any(item_loc, item)
            visitor.visit_set_end(loc, value)


class TypedMutableSetTypeHandler(BaseMutableSetTypeHandler):

    def __init__(self, typ: type[MutableSet], type_handler_factory: TypeHandlerFactory, /, **type_opts):
        super().__init__(typ)
        args = get_args(typ)
        if len(args) != 1:
            raise TypeError(f"unsupported type; got {typ!r}, expected MutableSet[T]")
        self._item_type_handler = type_handler_factory(args[0], **type_opts)

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        result = self.ensure_sequence_or_set(errors, loc, value)
        if is_unset(result):
            return Unset
        item_type_handler = self._item_type_handler
        parse_item = self._item_type_handler.parse
        result = {parse_item(errors, loc + Loc.irrelevant(), x) for x in result}
        if len(errors) > 0:
            return Unset
        return MutableSetProxy(self.typ, result, item_type_handler)

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        item_loc = loc + Loc.irrelevant()
        item_accept = self._item_type_handler.accept
        if visitor.visit_set_begin(loc, value) is not True:
            for item in value:
                item_accept(visitor, item_loc, item)
            visitor.visit_set_end(loc, value)


def create_mutable_set_type_handler(
    typ: type[MutableSet], type_handler_factory: TypeHandlerFactory, /, **type_opts
) -> TypeHandler:
    args = get_args(typ)
    if not args or args == (Any,):
        return AnyMutableSetTypeHandler(typ)
    return TypedMutableSetTypeHandler(typ, type_handler_factory, **type_opts)
