import functools

from typing import cast

from modelity.interface import IFieldHook, IFieldPostprocessingHook, IFieldPreprocessingHook, IFieldValidationHook, IModel, IModelHook, IModelPostvalidationHook, IModelPrevalidationHook


@functools.lru_cache
def _get_model_hooks_by_name(model_class: type[IModel], hook_name: str) -> list[IModelHook]:
    result = []
    for hook in model_class.__model_hooks__:
        if hook.__modelity_hook_name__ == hook_name:
            result.append(hook)
    return cast(list[IModelHook], result)


@functools.lru_cache
def _get_field_hooks_by_name(model_class: type[IModel], hook_name: str, field_name: str) -> list[IFieldHook]:
    result = []
    for hook in model_class.__model_hooks__:
        if hook.__modelity_hook_name__ == hook_name:
            hook = cast(IFieldHook, hook)
            field_names = hook.__modelity_hook_field_names__
            if len(field_names) == 0 or field_name in field_names:
                result.append(hook)
    return cast(list[IFieldHook], result)


def _get_model_prevalidation_hooks(model_class: type[IModel]) -> list[IModelPrevalidationHook]:
    return cast(
        list[IModelPrevalidationHook],
        _get_model_hooks_by_name(model_class, IModelPrevalidationHook.__modelity_hook_name__),
    )


def _get_model_postvalidation_hooks(model_class: type[IModel]) -> list[IModelPostvalidationHook]:
    return cast(
        list[IModelPostvalidationHook],
        _get_model_hooks_by_name(model_class, IModelPostvalidationHook.__modelity_hook_name__),
    )


def _get_field_validation_hooks(model_class: type[IModel], field_name: str) -> list[IFieldValidationHook]:
    return cast(
        list[IFieldValidationHook],
        _get_field_hooks_by_name(model_class, IFieldValidationHook.__modelity_hook_name__, field_name),
    )


def _get_field_preprocessing_hooks(model_class: type[IModel], field_name: str) -> list[IFieldPreprocessingHook]:
    return cast(
        list[IFieldPreprocessingHook],
        _get_field_hooks_by_name(model_class, IFieldPreprocessingHook.__modelity_hook_name__, field_name),
    )


def _get_field_postprocessing_hooks(model_class: type[IModel], field_name: str) -> list[IFieldPostprocessingHook]:
    return cast(
        list[IFieldPostprocessingHook],
        _get_field_hooks_by_name(model_class, IFieldPostprocessingHook.__modelity_hook_name__, field_name),
    )
