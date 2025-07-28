"""Module containing definitions of decorator functions that can be used to
inject user-defined hooks into model's data processing chain."""

import functools
from typing import Any, Callable, cast, Union, TypeVar

from modelity import _utils
from modelity.error import Error, ErrorFactory
from modelity.interface import (
    IModel,
    IModelHook,
    IFieldHook,
)
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType

__all__ = export = _utils.ExportList()  # type: ignore

T = TypeVar("T")


@export
def field_preprocessor(*field_names: str):
    """Decorate model's method as a field-level preprocessing hook.

    Value returned by preprocessor is either passed to the next preprocessor
    (if any) or to the type parser assigned for the field that is being set or
    modified.

    The decorated method can be defined with no arguments, or with any
    subsequence of the following arguments:

    **cls**
        The model type.

    **errors**
        Mutable list of errors.

        Can be extended by the preprocessor if preprocessing phase fails.
        Alternatively, preprocessor can raise :exc:`TypeError` exception that
        will automatically be converted into error and added to this list.

    **loc**
        The currently preprocessed model location.

        This is instance of the :class:`modelity.loc.Loc` type.

    **value**
        The input value for this preprocessor.

        This will either be user's input value, or the output value of previous
        preprocessor (if any).

    Here's an example use:

    .. testcode::

        from modelity.model import Model
        from modelity.hooks import field_preprocessor

        class Dummy(Model):
            foo: str

            @field_preprocessor("foo")
            def _strip_white_characters(value):
                if isinstance(value, str):
                    return value.strip()
                return value

    .. doctest::

        >>> dummy = Dummy(foo='  spam  ')
        >>> dummy
        Dummy(foo='spam')

    Check :ref:`guide-processing-preprocessing` for more details on how to use
    this hook.

    :param `*field_names`:
        List of field names.

        This can be left empty if the hook needs to be run for every field.

        Since hooks are inherited, this also includes subclasses of the
        model the hook was declared in and it is not checked in any way if
        field names are correct.
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
        given_param_names = _utils.extract_given_param_names_subsequence(func, supported_param_names)
        hook = cast(IFieldHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_name__ = field_preprocessor.__name__
        hook.__modelity_hook_field_names__ = set(field_names)
        return hook

    return decorator


@export
def field_postprocessor(*field_names: str):
    """Decorate model's method as a field-level postprocessing hook.

    Value returned by this kind of hook is either passed to a next
    postprocessor (if any), or stored as model's field final value. No
    additional type checking takes place after postprocessing stage, so the
    user must pay attention to this.

    The decorated method can be defined with no arguments, or with any
    subsequence of the following arguments:

    **cls**
        The model type.

    **self**
        The instance of the model that is currently being created or modified.

        This allows the hook to access other model's fields in a read-write way
        and can be used to either set related fields, or perform some
        additional on-field-change validation.

        .. important::

            The user needs to pay attention when accessing other fields, as
            those may have not been initialized yet. Modelity processes data
            field by field in field declaration order, so this must be taken
            into account when this functionality is used.

    **errors**
        Mutable list of errors.

        Can be extended by the postprocessor if postprocessing phase fails.
        Alternatively, postprocessor can raise :exc:`TypeError` exception that
        will automatically be converted into error and added to this list.

    **loc**
        The currently preprocessed model location.

        This is instance of the :class:`modelity.loc.Loc` type.

    **value**
        The input value for this postprocessor.

        This will either be the output value of the type parser, or the output
        value of previous postprocessor (if any).

    Here's an example use:

    .. testcode::

        from modelity.model import Model
        from modelity.hooks import field_postprocessor

        class FieldPostprocessorExample(Model):
            foo: str

            @field_postprocessor("foo")
            def _strip_white_characters(value):
                return value.strip()  # The 'value' is guaranteed to be str when this gets called

    Check :ref:`guide-processing-postprocessing` for more details on how to use
    this hook.

    :param `*field_names`:
        List of field names.

        This can be left empty if the hook needs to be run for every field.

        Since hooks are inherited, this also includes subclasses of the
        model the hook was declared in and it is not checked in any way if
        field names are correct.
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
        given_param_names = _utils.extract_given_param_names_subsequence(func, supported_param_names)
        hook = cast(IFieldHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_name__ = field_postprocessor.__name__
        hook.__modelity_hook_field_names__ = set(field_names)
        return hook

    return decorator


@export
def model_prevalidator():
    """Decorate model's method as a model-level prevalidation hook.

    The decorated method can be defined with no arguments, or with any
    subsequence of the following arguments:

    **cls**
        The model type.

    **self**
        The current model.

        Different than *root* means that this is a nested model.

    **root**
        The root model instance.

        This is the model for which :meth:`modelity.helpers.validate` was
        called. Can be used to access entire model when performing validation.

    **ctx**
        The user-defined validation context.

        Check :ref:`guide-validation-using_context` for more details.

    **errors**
        Mutable list of errors.

        Can be extended by this hook to signal validation errors.
        Alternatively, :exc:`ValueError` exception can be raised and will
        automatically be converted into error and added to this list.

    **loc**
        The location of the currently validated model.

        Will be empty if this is a root model, or non-empty if this model is
        nested inside another model.

        This is instance of the :class:`modelity.loc.Loc` type.

    Check :ref:`guide-validation-model_prevalidation` for more details on how
    to use this hook.
    """

    def decorator(func):
        return _make_model_validator(func, model_prevalidator.__name__)

    return decorator


@export
def model_postvalidator():
    """Decorate model's method as a model-level postvalidation hook.

    The arguments for the decorated method are exactly the same as for
    :func:`model_prevalidation` hook.

    Check :ref:`guide-validation-model_postvalidation` for more details on how
    to use this hook.
    """

    def decorator(func):
        return _make_model_validator(func, model_postvalidator.__name__)

    return decorator


@export
def field_validator(*field_names: str):
    """Decorate model's method as a field-level validator.

    This hook is executed for given field names only (or all fields, if the
    list of names is empty), if and only if the field is set and always in
    between model-level pre- and postvalidators.

    **cls**
        The model type.

    **self**
        The current model.

        Different than *root* means that this is a nested model.

    **root**
        The root model instance.

        This is the model for which :meth:`modelity.helpers.validate` was
        called. Can be used to access entire model when performing validation.

    **ctx**
        The user-defined validation context.

        Check :ref:`guide-validation-using_context` for more details.

    **errors**
        Mutable list of errors.

        Can be extended by this hook to signal validation errors.
        Alternatively, :exc:`ValueError` exception can be raised and will
        automatically be converted into error and added to this list.

    **loc**
        The location of the currently validated model.

        Will be empty if this is a root model, or non-empty if this model is
        nested inside another model.

        This is instance of the :class:`modelity.loc.Loc` type.

    **value**
        Field's value to validate.

    Check :ref:`guide-validation-field_validation` for more details on how
    to use this hook.
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
        given_param_names = _utils.extract_given_param_names_subsequence(func, supported_param_names)
        hook = cast(IFieldHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_name__ = field_validator.__name__
        hook.__modelity_hook_field_names__ = set(field_names)
        return hook

    return decorator


@export
def type_descriptor_factory(typ: Any):
    """Register type descriptor factory function for type *typ*.

    This decorator can be used to register non user-defined types (f.e. from
    3rd party libraries) that cannot be added to Modelity typing system via
    ``__modelity_type_descriptor__`` static function.

    Check :ref:`registering-3rd-party-types-label` for more details.

    .. note::
        This decorator must be used before first model is created or otherwise
        registered type might not be visible.

    .. versionadded:: 0.14.0

    :param typ:
        The type to register descriptor factory for.
    """
    from modelity._internal.type_descriptors.all import registry

    def decorator(func, /):
        return registry.register_type_descriptor_factory(typ, func)

    return decorator


def _make_model_validator(func: Callable, hook_name: str) -> IModelHook:

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
    given_param_names = _utils.extract_given_param_names_subsequence(func, supported_param_names)
    hook = cast(IModelHook, proxy)
    hook.__modelity_hook_id__ = _utils.next_unique_id()
    hook.__modelity_hook_name__ = hook_name
    return hook
