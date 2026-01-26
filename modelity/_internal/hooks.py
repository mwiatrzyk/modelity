import functools
from typing import Any, Iterator, Protocol, TypeGuard

from modelity.loc import Loc


class IBaseHook(Protocol):
    """Base class for hook protocols."""

    #: The sequential ID number assigned for this hook.
    #:
    #: This is used to sort hooks by their declaration order when they are
    #: collected from the model.
    __modelity_hook_id__: int

    #: The name of this hook.
    __modelity_hook_name__: str

    def __call__(self, *args: Any, **kwds: Any) -> Any: ...


class IModelHook(IBaseHook, Protocol):
    """Protocol describing model-level hooks."""


class IFieldHook(IBaseHook, Protocol):
    """Protocol describing field-level hooks."""

    #: Field names this hook will be used for.
    #:
    #: Empty set means that it will be used for all fields, non-empty set means
    #: that it will be used for a subset of model fields.
    __modelity_hook_field_names__: set[str]


class ILocationHook(IBaseHook, Protocol):
    """Protocol describing value-level, location specific hooks."""

    #: Set of value locations.
    #:
    #: Empty set means that this hook will match every single location.
    #: Non-empty meaning is implementation specific.
    __modelity_hook_value_locations__: set[Loc]


def is_base_hook(obj: object) -> TypeGuard[IBaseHook]:
    """Check if *obj* is instance of :class:`modelity.interface.IBaseHook` protocol."""
    return callable(obj) and hasattr(obj, "__modelity_hook_id__") and hasattr(obj, "__modelity_hook_name__")


def is_model_hook(obj: object) -> TypeGuard[IModelHook]:
    """Check if *obj* satisfies requirements of the :class:`IModelHook` protocol."""
    return is_base_hook(obj)


def is_field_hook(obj: object) -> TypeGuard[IFieldHook]:
    """Check if *obj* satisfies requirements of the :class:`IFieldHook` interface."""
    return is_model_hook(obj) and hasattr(obj, "__modelity_hook_field_names__")


def is_location_hook(obj: object) -> TypeGuard[ILocationHook]:
    """Check if *obj* satisfies requirements of the :class:`ILocationHook` interface."""
    return is_model_hook(obj) and hasattr(obj, "__modelity_hook_value_locations__")


def find_hooks_by_name(model_type: type, hook_name: str) -> Iterator[IBaseHook]:
    """Find all hooks with given name.

    :param model_type:
        The source model type.

    :param hook_name:
        The name to look for.
    """
    for hook in getattr(model_type, "_modelity_hooks", []):
        if not is_base_hook(hook):
            continue
        if hook.__modelity_hook_name__ == hook_name:
            yield hook


def find_field_hooks_by_name(model_type: type, hook_name: str, field_name: str) -> Iterator[IFieldHook]:
    """Find all field hooks with given name and registered for given field
    name.

    :param model_type:
        The source model type.

    :param hook_name:
        The hook name to look for.

    :param field_name:
        The field name to look for.
    """
    for hook in find_hooks_by_name(model_type, hook_name):
        if is_field_hook(hook):
            field_names = hook.__modelity_hook_field_names__
            if not field_names or field_name in field_names:
                yield hook


def collect_model_hooks(model_type: type, hook_name: str) -> list[IModelHook]:
    """Collect all model hooks.

    :param model_type:
        The source model type.

    :param hook_name:
        The model hook name to look for.
    """
    return _collect_model_hooks_impl(model_type, hook_name)


def collect_field_hooks(model_type: type, hook_name: str, field_name: str) -> list[IFieldHook]:
    """Collect all field hooks with given name and registered for given field
    name.

    :param model_type:
        The source model type.

    :param hook_name:
        The field hook name to look for.

    :param field_name:
        The field name to look for.
    """
    return _collect_field_hooks_impl(model_type, hook_name, field_name)


def collect_location_validator_hooks(model_type: type) -> dict[Loc, list[ILocationHook]]:
    """Collect all location validator hooks from given model.

    :param model_type:
        The source model type.
    """
    return _collect_location_validator_hooks(model_type)


@functools.lru_cache()
def _collect_model_hooks_impl(model_type: type, hook_name: str) -> list[IModelHook]:
    out = []
    for hook in find_hooks_by_name(model_type, hook_name):
        if is_model_hook(hook):
            out.append(hook)
    return out


@functools.lru_cache()
def _collect_field_hooks_impl(model_type: type, hook_name: str, field_name: str) -> list[IFieldHook]:
    out = []
    for hook in find_field_hooks_by_name(model_type, hook_name, field_name):
        out.append(hook)
    return out


@functools.lru_cache()
def _collect_location_validator_hooks(model_type: type) -> dict[Loc, list[ILocationHook]]:
    out: dict[Loc, list[ILocationHook]] = {}
    for hook in find_hooks_by_name(model_type, "location_validator"):
        if not is_location_hook(hook):
            continue
        location_suffix_patterns = hook.__modelity_hook_value_locations__
        if not location_suffix_patterns:
            out.setdefault(Loc(), []).append(hook)
        for pattern in location_suffix_patterns:
            out.setdefault(pattern, []).append(hook)
    return out
