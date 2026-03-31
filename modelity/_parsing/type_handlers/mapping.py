from typing import Any, Mapping, MutableMapping, get_args, get_origin

from modelity._parsing.type_proxies import MutableMappingProxy
from modelity.base import ModelVisitor, TypeHandler, TypeHandlerFactory
from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType, is_unset


class BaseMutableMappingTypeHandler(TypeHandler):
    typ: type[MutableMapping]

    def __init__(self, typ: type[MutableMapping]):
        origin = get_origin(typ)
        is_mutable_mapping = issubclass(typ, MutableMapping) if origin is None else issubclass(origin, MutableMapping)
        if not is_mutable_mapping:
            raise TypeError(f"unsupported type; got {typ!r}, expected MutableMapping")
        self.typ = typ

    def ensure_mapping(self, errors: list[Error], loc: Loc, value: Any) -> Mapping | UnsetType:
        if isinstance(value, Mapping):
            return value
        errors.append(ErrorFactory.invalid_type(loc, value, [self.typ], [Mapping]))
        return Unset


class AnyMutableMappingTypeHandler(BaseMutableMappingTypeHandler):

    def __init__(self, typ: type[MutableMapping]):
        super().__init__(typ)
        args = get_args(typ)
        if args and args != (Any, Any):
            raise TypeError(f"unsupported type; got {typ!r}, expected one of: MutableMapping, MutableMapping[Any, Any]")

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        result = self.ensure_mapping(errors, loc, value)
        if is_unset(result):
            return Unset
        return dict(result)

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visit_any = visitor.visit_any
        if visitor.visit_mapping_begin(loc, value) is not True:  # TODO: Use special SKIP sentinel
            for k, v in value.items():
                visit_any(loc + Loc(k), v)
            visitor.visit_mapping_end(loc, value)


class TypedMutableMappingTypeHandler(BaseMutableMappingTypeHandler):

    def __init__(self, typ: type[MutableMapping], type_handler_factory: TypeHandlerFactory, /, **type_opts):
        super().__init__(typ)
        args = get_args(typ)
        if len(args) != 2:
            raise TypeError(f"unsupported type; got {typ!r}, expected MutableMapping[K, V]")
        self._key_type_handler = type_handler_factory(args[0], **type_opts)
        self._value_type_handler = type_handler_factory(args[1], **type_opts)

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        result = self.ensure_mapping(errors, loc, value)
        if is_unset(result):
            return result
        key_type_handler = self._key_type_handler
        value_type_handler = self._value_type_handler
        parse_key = key_type_handler.parse
        parse_value = value_type_handler.parse
        irrelevant_loc = Loc.irrelevant()
        output = {}
        for key, value in result.items():
            key = parse_key(errors, loc + irrelevant_loc, key)
            if key is not Unset:
                output[key] = parse_value(errors, loc + Loc(key), value)
        if len(errors) > 0:
            return Unset
        return MutableMappingProxy(self.typ, output, key_type_handler, value_type_handler)

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        accept_item = self._value_type_handler.accept
        if visitor.visit_mapping_begin(loc, value) is not True:
            for k, v in value.items():
                accept_item(visitor, loc + Loc(k), v)
            visitor.visit_mapping_end(loc, value)


def create_mutable_mapping_type_handler(
    typ: type[MutableMapping], type_handler_factory: TypeHandlerFactory, /, **type_opts
) -> TypeHandler:
    args = get_args(typ)
    if not args or args == (Any, Any):
        return AnyMutableMappingTypeHandler(typ)
    return TypedMutableMappingTypeHandler(typ, type_handler_factory, **type_opts)
