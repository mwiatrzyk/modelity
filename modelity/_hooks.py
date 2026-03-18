import enum
from typing import Any, Literal, Mapping, Optional, Protocol, Sequence, cast

from typing_extensions import TypeIs

from modelity.error import Error
from modelity.loc import Loc, Pattern
from modelity.unset import UnsetType, is_unset


class HookType(enum.Enum):
    """Enumeration with supported hook types."""

    FIELD_PREPROCESSOR = "field_preprocessor"
    FIELD_POSTPROCESSOR = "field_postprocessor"
    MODEL_FIXUP = "model_fixup"
    FIELD_VALIDATOR = "field_validator"
    MODEL_PREVALIDATOR = "model_prevalidator"
    MODEL_POSTVALIDATOR = "model_postvalidator"
    LOCATION_VALIDATOR = "location_validator"


_field_hook_attr_map = {
    "_field_preprocessors": HookType.FIELD_PREPROCESSOR,
    "_field_postprocessors": HookType.FIELD_POSTPROCESSOR,
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
    return [x for x in all_hooks if x.__modelity_hook_type__ == hook_type and is_field_hook(x) and is_field_hook_for(x, field_name)]


def list_model_hooks(all_hooks: list[BaseHook], hook_type: HookType) -> list[ModelHook]:
    return [x for x in all_hooks if x.__modelity_hook_type__ == hook_type]


def list_location_hooks(all_hooks: list[BaseHook], hook_type: HookType) -> list[LocationHook]:
    return [x for x in all_hooks if is_location_hook(x) and x.__modelity_hook_type__ == hook_type]


def assign_field_hooks(field: Any, all_hooks: list[BaseHook], field_name: str):
    for attr_name, hook_type in _field_hook_attr_map.items():
        setattr(field, attr_name, list_field_hooks(all_hooks, hook_type, field_name))


def assign_model_hooks(model_type: type[Any], all_hooks: list[BaseHook]):
    for attr_name, hook_type in _model_hook_attr_map.items():
        setattr(model_type, attr_name, list_model_hooks(all_hooks, hook_type))


def assign_location_hooks(model_type: type[Any], all_hooks: list[BaseHook]):
    model_type._location_validators = list_location_hooks(all_hooks, HookType.LOCATION_VALIDATOR)


def run_field_preprocessors(field: Any, model_type: type, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
    for hook in cast(list[FieldHook], field._field_preprocessors):
        value = hook(model_type, errors, loc, value)
        if is_unset(value):
            return value
    return value


def run_field_postprocessors(
    field: Any, model_type: type[Any], model: Any, errors: list[Error], loc: Loc, value: Any
) -> Any | UnsetType:
    for hook in cast(list[FieldHook], field._field_postprocessors):
        value = hook(model_type, model, errors, loc, value)
        if is_unset(value):
            return value
    return value


def run_model_fixups(cls: type[Any], self: Any, loc: Loc):
    for hook in cast(list[ModelHook], cls._model_fixups):
        hook(cls, self, loc)


def run_field_validators(
    field: Any, model_type: type[Any], model: Any, root: Any, ctx: Any, errors: list[Error], loc: Loc, value: Any
):
    for hook in cast(list[FieldHook], field._field_validators):
        hook(model_type, model, root, ctx, errors, loc, value)


def run_model_prevalidators(model_type: type[Any], model: Any, root: Any, ctx: Any, errors: list[Error], loc: Loc) -> Optional[bool]:
    for hook in cast(list[ModelHook], model_type._model_prevalidators):
        if hook(model_type, model, root, ctx, errors, loc) is True:
            return True
    return None


def run_model_postvalidators(model_type: type[Any], model: Any, root: Any, ctx: Any, errors: list[Error], loc: Loc):
    for hook in cast(list[ModelHook], model_type._model_postvalidators):
        hook(model_type, model, root, ctx, errors, loc)


def run_location_validators(model_type: type[Any], model: Any, root: Any, ctx: Any, errors: list[Error], base_loc: Loc, loc: Loc, value: Any):
    for hook in cast(list[LocationHook], model_type._location_validators):
        for pattern in hook.__modelity_hook_patterns__:
            if Pattern(*base_loc, *pattern).match(loc):
                hook(model_type, model, root, ctx, errors, loc, value)
