"""Internal API for hook system."""

import functools
from typing import Any, Union
from typing_extensions import TypeGuard

from modelity.error import Error
from modelity.hooks import field_postprocessor, field_preprocessor
from modelity.interface import (
    IBaseHook,
    IFieldHook,
    IModel,
    IModelHook,
)
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType


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


def get_model_hooks(model_cls: type[IModel], hook_name: str) -> list[IModelHook]:
    """Get all model-level hooks named *hook_name* from provided model.."""
    return _get_model_hooks(model_cls, hook_name)


def get_field_hooks(model_cls: type[IModel], hook_name: str, field_name: str) -> list[IFieldHook]:
    """Get all field-level hooks named *hook_name*, registered for field named
    *field_name*, from provided model."""
    return _get_field_hooks(model_cls, hook_name, field_name)


def preprocess_field(cls: type[IModel], errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
    """Execute chain of field-level preprocessors.

    On successes, preprocessed value is returned.

    On failure, :obj:`modelity.unset.Unset` is returned and *errors* list
    is populated with preprocessing errors.

    :param cls:
        Model type.

    :param errors:
        Mutable list of errors.

    :param loc:
        The location in the model that is being preprocessed.

    :param value:
        Input value.
    """
    for hook in get_field_hooks(cls, field_preprocessor.__name__, loc[-1]):  # type: ignore
        value = hook(cls, errors, loc, value)
        if value is Unset:
            return Unset
    return value


def postprocess_field(cls: type[IModel], self: IModel, errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
    """Execute chain of field-level postprocessors.

    On success, value is returned.

    On failure, :obj:`modelity.unset.Unset` is returned and *errors* list
    is populated with postprocessing errors.

    :param cls:
        Model type.

    :param self:
        The model object.

        Postprocessors will use it to access other fields during model's
        construction and/or modification.

    :param errors:
        Mutable list of errors.

    :param loc:
        The location of the model that is being postprocessed.

    :param value:
        Input value.
    """
    for hook in get_field_hooks(cls, field_postprocessor.__name__, loc[-1]):  # type: ignore
        value = hook(cls, self, errors, loc, value)
        if value is Unset:
            return Unset
    return value


@functools.lru_cache()
def _get_model_hooks(model_cls: type[IModel], hook_name: str) -> list[IModelHook]:

    def gen():
        for hook in model_cls.__model_hooks__:
            if is_model_hook(hook) and hook.__modelity_hook_name__ == hook_name:
                yield hook

    return list(gen())


@functools.lru_cache()
def _get_field_hooks(model_cls: type[IModel], hook_name: str, field_name: str) -> list[IFieldHook]:

    def gen():
        for hook in model_cls.__model_hooks__:
            if is_field_hook(hook) and hook.__modelity_hook_name__ == hook_name:
                hook_field_names = hook.__modelity_hook_field_names__
                if not hook_field_names or field_name in hook_field_names:
                    yield hook

    return list(gen())
