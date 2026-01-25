from typing import Any, Iterator, Optional, Protocol, TypeVar, Union, cast

from modelity import _utils
from modelity.error import Error
from modelity.interface import IBaseHook, IFieldHook, ILocationHook, IModelHook, is_base_hook, is_field_hook, is_location_hook, is_model_hook
from modelity.loc import Loc
from modelity.unset import UnsetType


def find_hooks_by_name(model_type: type, hook_name: str) -> Iterator[IBaseHook]:
    for hook in getattr(model_type, "__model_hooks__", []):
        if not is_base_hook(hook):
            continue
        if hook.__modelity_hook_name__ == hook_name:
            yield hook


def find_field_hooks_by_name(model_type: type, hook_name: str, field_name: str) -> Iterator[IFieldHook]:
    for hook in find_hooks_by_name(model_type, hook_name):
        if is_field_hook(hook):
            field_names = hook.__modelity_hook_field_names__
            if not field_names or field_name in field_names:
                yield hook


def collect_model_hooks(model_type: type, hook_name: str) -> list[IModelHook]:
    out = []
    for hook in find_hooks_by_name(model_type, hook_name):
        if is_model_hook(hook):
            out.append(hook)
    return out


def collect_field_hooks(model_type: type, hook_name: str, field_name: str) -> list[IFieldHook]:
    out = []
    for hook in find_field_hooks_by_name(model_type, hook_name, field_name):
        out.append(hook)
    return out


def collect_location_validator_hooks(model_type: type) -> dict[Loc, list[ILocationHook]]:
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

