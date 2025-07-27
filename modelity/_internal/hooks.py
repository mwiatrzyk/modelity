"""Internal API for hook system."""

import functools
from typing import Iterator, cast
from pydantic import field_validator
from typing_extensions import TypeGuard

from modelity.hooks import field_postprocessor, field_preprocessor, model_postvalidator, model_prevalidator
from modelity.interface import (
    IFieldPostprocessingHook,
    IFieldPreprocessingHook,
    IFieldValidationHook,
    IModel,
    IModelFieldHook,
    IModelHook,
    IModelValidationHook,
)


def is_model_hook(obj: object) -> TypeGuard[IModelHook]:
    """Check if *obj* is instance of :class:`modelity.interface.IModelHook`
    protocol."""
    return callable(obj) and hasattr(obj, "__modelity_hook_id__") and hasattr(obj, "__modelity_hook_name__")


def get_field_preprocessors(model_type: type[IModel], field_name: str) -> list[IFieldPreprocessingHook]:
    return cast(list[IFieldPreprocessingHook], _list_field_hooks(model_type, field_preprocessor.__name__, field_name))


def get_field_postprocessors(model_type: type[IModel], field_name: str) -> list[IFieldPostprocessingHook]:
    return cast(list[IFieldPostprocessingHook], _list_field_hooks(model_type, field_postprocessor.__name__, field_name))


def get_model_prevalidators(model_type: type[IModel]) -> list[IModelValidationHook]:
    return cast(list[IModelValidationHook], _list_model_hooks(model_type, model_prevalidator.__name__))


def get_model_postvalidators(model_type: type[IModel]) -> list[IModelValidationHook]:
    return cast(list[IModelValidationHook], _list_model_hooks(model_type, model_postvalidator.__name__))


def get_field_validators(model_type: type[IModel], field_name: str) -> list[IFieldValidationHook]:
    return cast(list[IFieldValidationHook], _list_field_hooks(model_type, field_validator.__name__, field_name))


def _is_field_hook(obj: object) -> TypeGuard[IModelFieldHook]:
    return is_model_hook(obj) and hasattr(obj, "__modelity_hook_field_names__")


def _iter_model_hooks(model_type: type[IModel], hook_name: str) -> Iterator[IModelHook]:
    for model_hook in model_type.__model_hooks__:
        if model_hook.__modelity_hook_name__ == hook_name:
            yield model_hook


def _iter_field_hooks(model_type: type[IModel], hook_name: str, field_name: str) -> Iterator[IModelFieldHook]:
    for model_hook in _iter_model_hooks(model_type, hook_name):
        if _is_field_hook(model_hook):
            hook_field_names = model_hook.__modelity_hook_field_names__
            if not hook_field_names or field_name in hook_field_names:
                yield model_hook


@functools.lru_cache()
def _list_model_hooks(model_type: type[IModel], hook_name: str) -> list[IModelHook]:
    return list(_iter_model_hooks(model_type, hook_name))


@functools.lru_cache()
def _list_field_hooks(model_type: type[IModel], hook_name: str, field_name: str) -> list[IModelFieldHook]:
    return list(_iter_field_hooks(model_type, hook_name, field_name))
