from typing import Annotated, Any, Union, get_args, get_origin

from modelity import _utils
from modelity.base import TypeHandlerWithValidation, Constraint, ModelVisitor, TypeHandler, TypeHandlerFactory
from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.types import is_deferred, is_loose_optional, is_optional, is_strict_optional
from modelity.unset import Unset, UnsetType, is_unset


class AnnotatedTypeHandler(TypeHandlerWithValidation):

    def __init__(self, typ: Any, type_handler_factory: TypeHandlerFactory, /, **type_opts):
        origin = get_origin(typ)
        if origin is not Annotated:
            raise TypeError(f"expected Annotated[T, ...], got {typ!r} instead")
        args = get_args(typ)
        assert len(args) > 1  # Always True for Annotated[T, ...]
        self._constraints = [self._ensure_constraint(x) for x in args[1:]]
        self._type_handler = type_handler_factory(args[0], **type_opts)

    @staticmethod
    def _ensure_constraint(obj: Any) -> Constraint:
        if not isinstance(obj, Constraint):
            raise TypeError(f"expected Constraint, got {obj!r} instead")
        return obj

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        result = self._type_handler.parse(errors, loc, value)
        if is_unset(result):
            return result
        self.validate(errors, loc, result)
        if len(errors) > 0:
            return Unset
        return result

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        self._type_handler.accept(visitor, loc, value)

    def validate(self, errors: list[Error], loc: Loc, value: Any) -> bool:
        for constraint in self._constraints:
            if not constraint.validate(errors, loc, value):
                return False
        return True


class DeferredTypeHandler(TypeHandlerWithValidation):

    def __init__(self, typ: Any, type_handler_factory: TypeHandlerFactory, /, **type_opts):
        if not is_deferred(typ):
            raise TypeError(f"expected Deferred[T], got {typ!r} instead")
        deferred_type = get_args(typ)[0]
        types = get_args(deferred_type)[:-1]  # Strip UnsetType; it will be handled separately
        if len(types) == 0:
            raise TypeError("expected Deferred[T], got Deferred with no type")
        self._typ = types[0] if len(types) == 1 else _utils.make_union_type(types)
        self._inner_type_handler = type_handler_factory(self._typ, **type_opts)

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if is_unset(value):
            return value
        return self._inner_type_handler.parse(errors, loc, value)

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        if is_unset(value):
            visitor.visit_unset(loc, value)
        else:
            self._inner_type_handler.accept(visitor, loc, value)

    def validate(self, errors: list[Error], loc: Loc, value: Any) -> bool:
        if is_unset(value):
            errors.append(ErrorFactory.unset_not_allowed(loc, self._typ))
            return False
        if isinstance(self._inner_type_handler, TypeHandlerWithValidation):
            return self._inner_type_handler.validate(errors, loc, value)
        return True


def create_annotated_type_handler(typ: Any, type_handler_factory: TypeHandlerFactory, /, **type_opts) -> TypeHandler:
    if is_deferred(typ):
        return DeferredTypeHandler(typ, type_handler_factory, **type_opts)
    return AnnotatedTypeHandler(typ, type_handler_factory, **type_opts)


class OptionalTypeHandler(TypeHandler):

    def __init__(self, typ: Any, type_handler_factory: TypeHandlerFactory, /, **type_opts):
        self._typ = typ
        if not is_optional(typ):
            raise TypeError(f"expected Optional[T], got {_utils.describe(typ)} instead")
        args = get_args(typ)
        self._inner_type_handler = type_handler_factory(args[0], **type_opts)

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if value is None:
            return value
        if value is Unset:
            errors.append(ErrorFactory.unset_not_allowed(loc, self._typ))
            return Unset
        return self._inner_type_handler.parse(errors, loc, value)

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        if value is None:
            return visitor.visit_none(loc, value)
        self._inner_type_handler.accept(visitor, loc, value)


class LooseOptionalTypeHandler(TypeHandler):

    def __init__(self, typ: Any, type_handler_factory: TypeHandlerFactory, /, **type_opts):
        if not is_loose_optional(typ):
            raise TypeError(f"expected LooseOptional[T], got {_utils.describe(typ)} instead")
        args = get_args(typ)
        self._inner_type_handler = type_handler_factory(args[0], **type_opts)

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if value in {Unset, None}:
            return value
        return self._inner_type_handler.parse(errors, loc, value)

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        if value is Unset:
            return visitor.visit_unset(loc, value)
        if value is None:
            return visitor.visit_none(loc, value)
        return self._inner_type_handler.accept(visitor, loc, value)


class StrictOptionalTypeHandler(TypeHandler):

    def __init__(self, typ: Any, type_handler_factory: TypeHandlerFactory, /, **type_opts):
        self._typ = typ
        if not is_strict_optional(typ):
            raise TypeError(f"expected StrictOptional[T], got {_utils.describe(typ)} instead")
        args = get_args(typ)
        self._inner_type_handler = type_handler_factory(args[0], **type_opts)

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if value is Unset:
            return value
        if value is None:
            errors.append(ErrorFactory.none_not_allowed(loc, self._typ))
            return Unset
        return self._inner_type_handler.parse(errors, loc, value)

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        if value is Unset:
            return visitor.visit_unset(loc, value)
        self._inner_type_handler.accept(visitor, loc, value)


class UnionTypeHandler(TypeHandler):

    def __init__(self, typ: Any, type_handler_factory: TypeHandlerFactory, /, **type_opts):
        origin = get_origin(typ)
        if origin is not Union:
            raise TypeError(f"expected Union[T, ...], got {_utils.describe(typ)} instead")
        self._inner_types = get_args(typ)
        self._inner_type_handlers = [type_handler_factory(t, **type_opts) for t in self._inner_types]

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        # TODO: Maybe add configurable strategies for unions?
        for inner_type in self._inner_types:
            if isinstance(value, inner_type):
                return value
        inner_errors: list[Error] = []
        for inner_type_handler in self._inner_type_handlers:
            result = inner_type_handler.parse(inner_errors, loc, value)
            if result is not Unset:
                return result
        errors.append(ErrorFactory.invalid_type(loc, value, list(self._inner_types)))
        return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        for inner_type, inner_type_handler in zip(self._inner_types, self._inner_type_handlers):
            if isinstance(value, inner_type):
                return inner_type_handler.accept(visitor, loc, value)
        else:
            visitor.visit_any(loc, value)  # Fallback; f.e. when postprocessor has modified the type


def create_union_type_handler(typ: Any, type_handler_factory: TypeHandlerFactory, /, **type_opts) -> TypeHandler:
    if is_optional(typ):
        return OptionalTypeHandler(typ, type_handler_factory, **type_opts)
    if is_loose_optional(typ):
        return LooseOptionalTypeHandler(typ, type_handler_factory, **type_opts)
    if is_strict_optional(typ):
        return StrictOptionalTypeHandler(typ, type_handler_factory, **type_opts)
    return UnionTypeHandler(typ, type_handler_factory, **type_opts)
