"""Internal API for hook system."""

import functools
from typing_extensions import TypeGuard

from modelity.interface import (
    IBaseHook,
    IFieldHook,
    IModelHook,
)


def is_base_hook(obj: object) -> TypeGuard[IBaseHook]:
    """Check if *obj* is instance of :class:`modelity.interface.IBaseHook`
    protocol."""
    return callable(obj) and hasattr(obj, "__modelity_hook_id__") and hasattr(obj, "__modelity_hook_name__")


def is_model_hook(obj: object) -> TypeGuard[IModelHook]:
    """Check if *obj* is instance of :class:`modelity.interface.IModelHook`
    protocol."""
    return is_base_hook(obj)


def is_field_hook(obj: object) -> TypeGuard[IFieldHook]:
    """Check if *obj* is instance of :class:`modelity.interface.IFieldHook`
    protocol."""
    return is_base_hook(obj) and hasattr(obj, "__modelity_hook_field_names__")


def get_model_hooks(model_cls: type, hook_name: str) -> list[IModelHook]:
    """Get all model-level hooks named *hook_name* from provided model.."""
    return _get_model_hooks(model_cls, hook_name)


def get_field_hooks(model_cls: type, hook_name: str, field_name: str) -> list[IFieldHook]:
    """Get all field-level hooks named *hook_name*, registered for field named
    *field_name*, from provided model."""
    return _get_field_hooks(model_cls, hook_name, field_name)


@functools.lru_cache()
def _get_model_hooks(model_cls: type, hook_name: str) -> list[IModelHook]:

    def gen():
        for hook in getattr(model_cls, "__model_hooks__", []):
            if is_model_hook(hook) and hook.__modelity_hook_name__ == hook_name:
                yield hook

    return list(gen())


@functools.lru_cache()
def _get_field_hooks(model_cls: type, hook_name: str, field_name: str) -> list[IFieldHook]:

    def gen():
        for hook in getattr(model_cls, "__model_hooks__", []):
            if is_field_hook(hook) and hook.__modelity_hook_name__ == hook_name:
                hook_field_names = hook.__modelity_hook_field_names__
                if not hook_field_names or field_name in hook_field_names:
                    yield hook

    return list(gen())
