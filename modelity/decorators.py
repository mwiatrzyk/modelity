import functools
import inspect
from typing import Any, Callable, Iterator, Sequence, cast, Union, TypeVar

from modelity import _utils
from modelity.error import Error, ErrorFactory
from modelity.interface import (
    IFieldPostprocessingHook,
    IFieldPreprocessingHook,
    IFieldValidationHook,
    IModel,
    IModelHook,
    IModelFieldHook,
    IModelValidationHook,
)
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType

MH = TypeVar("MH", bound=IModelHook)

FH = TypeVar("FH", bound=IModelFieldHook)


def field_preprocessor(*field_names: str):
    """Decorate model's method as a field preprocessing hook.

    Field preprocessors allow to execute user-defined filtering (like white
    character stripping) before value is passed further to the type parser.

    Check :class:`modelity.interface.IFieldParsingHook` protocol for more
    details.

    Here's an example use:

    .. testcode::

        from modelity.model import Model, field_preprocessor

        class FieldPreprocessorExample(Model):
            foo: str

            @field_preprocessor("foo")
            def _strip_white_characters(value):
                if isinstance(value, str):
                    return value.strip()
                return value

    :param `*field_names`:
        List of field names this preprocessor will be called for.

        If not set, then it will be called for every field.
    """

    def decorator(func: Callable):

        @functools.wraps(func)
        def proxy(cls: type[IModel], errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
            kw: dict[str, Any] = {}
            if "cls" in given_param_names:
                kw["cls"] = cls
            if "errors" in given_param_names:
                kw["errors"] = errors
            if "loc" in given_param_names:
                kw["loc"] = loc
            if "value" in given_param_names:
                kw["value"] = value
            try:
                return func(**kw)
            except TypeError as e:
                errors.append(ErrorFactory.exception(loc, str(e), type(e)))
                return Unset

        supported_param_names = ("cls", "errors", "loc", "value")
        given_param_names = _extract_and_validate_given_param_names(func, supported_param_names)
        hook = cast(IFieldPreprocessingHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_name__ = field_preprocessor.__name__
        hook.__modelity_hook_field_names__ = set(field_names)
        return hook

    return decorator


def field_postprocessor(*field_names: str):
    """Decorate model's method as field postprocessing hook.

    Field postprocessors are executed just after value parsing and only if the
    parsing was successful. Postprocessing is the last step of value processing
    and can be used to perform additional user-defined and field-specific
    validation. Value returned by postprocessor is used as input value for
    another postprocessor if there are many postprocessors defined for a single
    field. Value returned by last postprocessor becomes final field's value.

    Check :class:`modelity.interface.IFieldParsingHook` protocol for the list
    of supported arguments and their meaning.

    Here's an example use:

    .. testcode::

        from modelity.model import Model, field_postprocessor

        class FieldPostprocessorExample(Model):
            foo: str

            @field_postprocessor("foo")
            def _strip_white_characters(value):
                return value.strip()  # The 'value' is guaranteed to be str when this gets called

    :param `*field_names`:
        List of field names this postprocessor will be called for.

        If not set, then it will be called for every field.
    """

    def decorator(func):

        @functools.wraps(func)
        def proxy(cls: type[IModel], self: IModel, errors: list[Error], loc: Loc, value: Any) -> Union[Any, UnsetType]:
            kw: dict[str, Any] = {}
            if "cls" in given_param_names:
                kw["cls"] = cls
            if "self" in given_param_names:
                kw["self"] = self
            if "errors" in given_param_names:
                kw["errors"] = errors
            if "loc" in given_param_names:
                kw["loc"] = loc
            if "value" in given_param_names:
                kw["value"] = value
            try:
                return func(**kw)
            except TypeError as e:
                errors.append(ErrorFactory.exception(loc, str(e), type(e)))
                return Unset

        supported_param_names = ("cls", "self", "errors", "loc", "value")
        given_param_names = _extract_and_validate_given_param_names(func, supported_param_names)
        hook = cast(IFieldPostprocessingHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_name__ = field_postprocessor.__name__
        hook.__modelity_hook_field_names__ = set(field_names)
        return hook

    return decorator


def model_prevalidator():
    """Decorate model's method as a model prevalidator.

    Prevalidators run before any other validators (including built-in ones),
    during the initial stage of model validation.

    Check :class:`modelity.interface.IModelValidationHook` protocol for the
    list of supported arguments that can be used by the decorated method.
    """

    def decorator(func):
        return _make_model_validator(func, model_prevalidator.__name__)

    return decorator


def model_postvalidator():
    """Decorate model's method as a model postvalidator.

    Postvalidators run after all other validators, during the final stage of
    model validation.

    Check :class:`modelity.interface.IModelValidationHook` protocol for the
    list of supported arguments that can be used by the decorated method.
    """

    def decorator(func):
        return _make_model_validator(func, model_postvalidator.__name__)

    return decorator


def field_validator(*field_names: str):
    """Decorate model's method as a field validator.

    Unlike model pre- and postvalidators, operating in the model scope, field
    validators are only executed if the field has value assigned. And since the
    value must pass parsing step, field validators can safely assume that the
    value already has correct type.

    Check :class:`modelity.interface.IFieldValidationHook` protocol for the
    list of supported method arguments and their meaning.

    :param `*field_names`:    func: Callable
    supported_param_names: tuple[str, ...]
    given_param_names: set[str]
        Names of fields to run this validator for.

        Leave empty to run for all fields defined in the current model.
    """

    def decorator(func):

        @functools.wraps(func)
        def proxy(cls: type[IModel], self: IModel, root: IModel, ctx: Any, errors: list[Error], loc: Loc, value: Any):
            given_params = given_param_names
            kw: dict[str, Any] = {}
            if "cls" in given_params:
                kw["cls"] = cls
            if "self" in given_params:
                kw["self"] = self
            if "root" in given_params:
                kw["root"] = root
            if "ctx" in given_params:
                kw["ctx"] = ctx
            if "errors" in given_params:
                kw["errors"] = errors
            if "loc" in given_params:
                kw["loc"] = loc
            if "value" in given_params:
                kw["value"] = value
            try:
                func(**kw)
            except ValueError as e:
                errors.append(ErrorFactory.exception(loc, str(e), type(e)))

        supported_param_names = ("cls", "self", "root", "ctx", "errors", "loc", "value")
        given_param_names = _extract_and_validate_given_param_names(func, supported_param_names)
        hook = cast(IFieldValidationHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_name__ = field_validator.__name__
        hook.__modelity_hook_field_names__ = set(field_names)
        return hook

    return decorator


def _make_model_validator(func: Callable, hook_name: str) -> IModelValidationHook:

    @functools.wraps(func)
    def proxy(cls: type[IModel], self: IModel, root: IModel, ctx: Any, errors: list[Error], loc: Loc):
        given_params = given_param_names
        kw: dict[str, Any] = {}
        if "cls" in given_params:
            kw["cls"] = cls
        if "self" in given_params:
            kw["self"] = self
        if "root" in given_params:
            kw["root"] = root
        if "ctx" in given_params:
            kw["ctx"] = ctx
        if "errors" in given_params:
            kw["errors"] = errors
        if "loc" in given_params:
            kw["loc"] = loc
        try:
            func(**kw)
        except ValueError as e:
            errors.append(ErrorFactory.exception(loc, str(e), type(e)))

    supported_param_names = ("cls", "self", "root", "ctx", "errors", "loc")
    given_param_names = _extract_and_validate_given_param_names(func, supported_param_names)
    hook = cast(IModelValidationHook, proxy)
    hook.__modelity_hook_id__ = _utils.next_unique_id()
    hook.__modelity_hook_name__ = hook_name
    return hook


def list_model_hooks(model_type: type[IModel], hook_type: type[MH]) -> list[MH]:
    """Get an ordered list of model hooks declared in provided model type.

    If no hooks are found, then empty list is returned.

    :param model_type:
        Model class to look for hooks in.

    :param hook_type:
        The type of model hook to look for.
    """
    found = []
    for hook in model_type.__model_hooks__:
        if isinstance(hook, IModelHook) and isinstance(hook, hook_type):
            found.append(hook)
    return found


def _is_model_hook(func: Callable) -> bool:
    return hasattr(func, "__modelity_hook_id__") and hasattr(func, "__modelity_hook_name__")


def _iter_field_hooks(model_type: type[IModel], hook_name: str, field_name: str) -> Iterator[IModelFieldHook]:
    for model_hook in _iter_model_hooks(model_type, hook_name):
        field_hook = cast(IModelFieldHook, model_hook)
        try:
            hook_field_names = field_hook.__modelity_hook_field_names__
        except AttributeError:
            continue  # Not a field hook
        if not hook_field_names or field_name in hook_field_names:
            yield field_hook


def _iter_model_hooks(model_type: type[IModel], hook_name: str) -> Iterator[IModelHook]:
    for model_hook in model_type.__model_hooks__:
        if model_hook.__modelity_hook_name__ == hook_name:
            yield model_hook


@functools.lru_cache()
def _list_model_hooks(model_type: type[IModel], hook_name: str) -> list[IModelHook]:
    return list(_iter_model_hooks(model_type, hook_name))


@functools.lru_cache()
def _list_field_hooks(model_type: type[IModel], hook_name: str, field_name: str) -> list[IModelFieldHook]:
    return list(_iter_field_hooks(model_type, hook_name, field_name))


def _get_field_preprocessors(model_type: type[IModel], field_name: str) -> list[IFieldPreprocessingHook]:
    return cast(list[IFieldPreprocessingHook], _list_field_hooks(model_type, field_preprocessor.__name__, field_name))


def _get_field_postprocessors(model_type: type[IModel], field_name: str) -> list[IFieldPostprocessingHook]:
    return cast(list[IFieldPostprocessingHook], _list_field_hooks(model_type, field_postprocessor.__name__, field_name))


def _get_model_prevalidators(model_type: type[IModel]) -> list[IModelValidationHook]:
    return cast(list[IModelValidationHook], _list_model_hooks(model_type, model_prevalidator.__name__))


def _get_model_postvalidators(model_type: type[IModel]) -> list[IModelValidationHook]:
    return cast(list[IModelValidationHook], _list_model_hooks(model_type, model_postvalidator.__name__))


def _get_field_validators(model_type: type[IModel], field_name: str) -> list[IFieldValidationHook]:
    return cast(list[IFieldValidationHook], _list_field_hooks(model_type, field_validator.__name__, field_name))


def _extract_and_validate_given_param_names(func: Callable, supported_param_names: Sequence[str]) -> set[str]:
    sig = inspect.signature(func)
    given_param_names = tuple(sig.parameters)
    if not _utils.is_subsequence(given_param_names, supported_param_names):
        raise TypeError(
            f"hook function {func.__name__!r} has incorrect signature: "
            f"{_utils.format_signature(given_param_names)} is not a subsequence of {_utils.format_signature(supported_param_names)}"
        )
    return set(given_param_names)
