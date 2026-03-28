import enum
from typing import Any, Callable, Optional, Protocol, cast

from typing_extensions import TypeIs

from modelity.error import Error, ErrorFactory
from modelity.exc import UserError
from modelity.loc import Loc, Pattern
from modelity.unset import Unset, UnsetType, is_unset


class HookType(enum.Enum):
    """Enumeration with supported hook types."""

    FIELD_PREPROCESSOR = "field_preprocessor"
    FIELD_POSTPROCESSOR = "field_postprocessor"
    MODEL_FIXUP = "model_fixup"
    FIELD_FIXUP = "field_fixup"
    FIELD_VALIDATOR = "field_validator"
    MODEL_PREVALIDATOR = "model_prevalidator"
    MODEL_POSTVALIDATOR = "model_postvalidator"
    LOCATION_VALIDATOR = "location_validator"


_field_hook_attr_map = {
    "_field_preprocessors": HookType.FIELD_PREPROCESSOR,
    "_field_postprocessors": HookType.FIELD_POSTPROCESSOR,
    "_field_fixups": HookType.FIELD_FIXUP,
    "_field_validators": HookType.FIELD_VALIDATOR,
}


_model_hook_attr_map = {
    "_model_fixups": HookType.MODEL_FIXUP,
    "_model_prevalidators": HookType.MODEL_PREVALIDATOR,
    "_model_postvalidators": HookType.MODEL_POSTVALIDATOR,
}


class BaseHook(Protocol):
    """Base protocol for user hooks."""

    #: Hook sequential ID number.
    #:
    #: Can be used to order hooks according to their declaration order which
    #: should also be hook execution order.
    __modelity_hook_id__: int

    #: The type of this hook.
    __modelity_hook_type__: HookType

    def __call__(self, *args: Any, **kwds: Any) -> Any: ...


class ModelHook(BaseHook, Protocol):
    """Protocol describing hooks operating on model level."""


class FieldHook(BaseHook, Protocol):
    """Protocol describing hooks operating on field level."""

    #: Set of field names this hook was declared for.
    #:
    #: An empty set means that the hook will be used for all fields of the
    #: current model.
    __modelity_hook_field_names__: set[str]


class LocationHook(BaseHook, Protocol):
    """Protocol describing value-oriented hooks operating on matched locations."""

    #: Set of value location patterns.
    #:
    #: Empty set is matched to any location, non-empty set defines location
    #: patterns that will cause hook execution once matched to the current
    #: location.
    __modelity_hook_patterns__: set[Pattern]


def is_hook(obj: Any) -> TypeIs[BaseHook]:
    return hasattr(obj, "__modelity_hook_id__") and hasattr(obj, "__modelity_hook_type__")


def is_field_hook(obj: BaseHook) -> TypeIs[FieldHook]:
    return hasattr(obj, "__modelity_hook_field_names__")


def is_location_hook(obj: BaseHook) -> TypeIs[LocationHook]:
    return hasattr(obj, "__modelity_hook_patterns__")


def is_field_hook_for(obj: FieldHook, field_name: str) -> bool:
    return len(obj.__modelity_hook_field_names__) == 0 or field_name in obj.__modelity_hook_field_names__


def list_field_hooks(all_hooks: list[BaseHook], hook_type: HookType, field_name: str) -> list[FieldHook]:
    return [
        x
        for x in all_hooks
        if x.__modelity_hook_type__ == hook_type and is_field_hook(x) and is_field_hook_for(x, field_name)
    ]


def list_model_hooks(all_hooks: list[BaseHook], hook_type: HookType) -> list[ModelHook]:
    return [x for x in all_hooks if x.__modelity_hook_type__ == hook_type]


def list_location_hooks(all_hooks: list[BaseHook], hook_type: HookType) -> list[LocationHook]:
    return [x for x in all_hooks if is_location_hook(x) and x.__modelity_hook_type__ == hook_type]


def assign_field_hooks(field: Any, all_hooks: list[BaseHook], field_name: str):
    for attr_name, hook_type in _field_hook_attr_map.items():
        setattr(field, attr_name, list_field_hooks(all_hooks, hook_type, field_name))


def assign_model_hooks(cls: type[Any], all_hooks: list[BaseHook]):
    for attr_name, hook_type in _model_hook_attr_map.items():
        setattr(cls, attr_name, list_model_hooks(all_hooks, hook_type))


def assign_location_hooks(cls: type[Any], all_hooks: list[BaseHook]):
    cls._location_validators = list_location_hooks(all_hooks, HookType.LOCATION_VALIDATOR)


def run_field_preprocessor_hooks(field: Any, cls: type, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
    return _run_field_processors(cast(list[FieldHook], field._field_preprocessors), cls, errors, loc, value)


def run_field_postprocessor_hooks(
    field: Any, cls: type[Any], errors: list[Error], loc: Loc, value: Any
) -> Any | UnsetType:
    return _run_field_processors(cast(list[FieldHook], field._field_postprocessors), cls, errors, loc, value)


def run_after_field_set_hooks(field: Any, cls: type[Any], self: Any, loc: Loc, value: Any):
    for hook in cast(list[FieldHook], field._field_fixups):
        hook(cls, self, loc, value)


def run_model_fixup_hooks(cls: type[Any], self: Any, root: Any, ctx: Any, loc: Loc):
    for hook in cast(list[ModelHook], cls._model_fixups):
        hook(cls, self, root, ctx, loc)


def run_field_validator_hooks(
    field: Any, cls: type[Any], self: Any, root: Any, ctx: Any, errors: list[Error], loc: Loc, value: Any
):
    for hook in cast(list[FieldHook], field._field_validators):
        _run_validation_hook(lambda: hook(cls, self, root, ctx, errors, loc, value), errors, loc, value)


def run_model_prevalidator_hooks(
    cls: type[Any], self: Any, root: Any, ctx: Any, errors: list[Error], loc: Loc
) -> Optional[bool]:
    for hook in cast(list[ModelHook], cls._model_prevalidators):
        if _run_validation_hook(lambda: hook(cls, self, root, ctx, errors, loc), errors, loc) is True:
            return True
    return None


def run_model_postvalidator_hooks(cls: type[Any], self: Any, root: Any, ctx: Any, errors: list[Error], loc: Loc):
    for hook in cast(list[ModelHook], cls._model_postvalidators):
        _run_validation_hook(lambda: hook(cls, self, root, ctx, errors, loc), errors, loc)


def run_location_validator_hooks(
    cls: type[Any], self: Any, root: Any, ctx: Any, errors: list[Error], base_loc: Loc, loc: Loc, value: Any
):
    for hook in cast(list[LocationHook], cls._location_validators):
        for pattern in hook.__modelity_hook_patterns__:
            if Pattern(*base_loc, *pattern).match(loc):
                _run_validation_hook(lambda: hook(cls, self, root, ctx, errors, loc, value), errors, loc, value)


def _run_field_processors(
    hooks: list[FieldHook], cls: type[Any], errors: list[Error], loc: Loc, value: Any
) -> Any | UnsetType:
    for hook in hooks:
        value = _run_processing_hook(lambda: hook(cls, errors, loc, value), errors, loc, value)
        if is_unset(value):
            return value
    return value


def _run_processing_hook(hook: Callable, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
    try:
        return hook()
    except UserError as e:
        errors.append(_error_from_user_error(e, loc, value))
        return Unset
    except TypeError as e:
        errors.append(ErrorFactory.exception(loc, value, e))
        return Unset


def _run_validation_hook(func: Callable, errors: list[Error], loc: Loc, value: Any = Unset) -> Any:
    try:
        return func()
    except UserError as e:
        errors.append(_error_from_user_error(e, loc, value))
        if e.skip:
            return True
    except ValueError as e:
        errors.append(ErrorFactory.exception(loc, value, e))


def _error_from_user_error(exc: UserError, loc: Loc, value: Any = Unset) -> Error:
    data = exc.data or {}
    if exc.loc is not None:
        loc = exc.loc
    if exc.value is not Unset:
        value = exc.value
    return Error(loc, exc.code, exc.msg, value, data)
