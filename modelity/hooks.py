"""Module containing definitions of decorator functions that can be used to
inject user-defined hooks into model's data processing chain."""

import functools
import textwrap
from typing import Any, Callable, Sequence, cast, TypeVar

from modelity import _export_list, _utils, _hooks
from modelity.loc import Loc, Pattern
from modelity.base import Model

__all__ = export = _export_list.ExportList()  # type: ignore

T = TypeVar("T")


@export
def field_preprocessor(*field_names: str):
    """Decorate model's method as a field-level preprocessing hook.

    Field preprocessors are used to filter input value on a field-specific
    basis before it is parsed to a target type. For example, this hook can be
    used to strip string input from white characters.

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

        from modelity.base import Model
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

    :param `*field_names`:
        List of field names.

        This can be left empty if the hook needs to be run for every field.

        Since hooks are inherited, this also includes subclasses of the
        model the hook was declared in and it is not checked in any way if
        field names are correct.
    """

    def decorator(func: Callable):
        return _make_field_processor(func, _hooks.HookType.FIELD_PREPROCESSOR, field_names)

    return decorator


@export
def field_postprocessor(*field_names: str):
    """Decorate model's method as a field-level postprocessing hook.

    Field postprocessors are only executed after successful preprocessing and
    parsing stages for the field they are declared for. Use this hook to
    perform additional per-field validation (executed when field is set or
    modified), or data normalization. Input value received by this hook is
    already parsed to a valid type and no other checking regarding this matter
    needs to take place.

    Value returned by this kind of hook is either passed to a next
    postprocessor (if any), or stored as model's field final value. No
    additional type checking takes place after postprocessing stage, so the
    user must pay attention to this.

    The decorated method can be defined with no arguments, or with any
    subsequence of the following arguments:

    **cls**
        The model type.

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

        from modelity.base import Model
        from modelity.hooks import field_postprocessor

        class FieldPostprocessorExample(Model):
            foo: str

            @field_postprocessor("foo")
            def _strip_white_characters(value):
                return value.strip()  # The 'value' is guaranteed to be str when this gets called

    :param `*field_names`:
        List of field names.

        This can be left empty if the hook needs to be run for every field.

        Since hooks are inherited, this also includes subclasses of the
        model the hook was declared in and it is not checked in any way if
        field names are correct.

    .. versionchanged:: 0.37.0
        Removed **self** argument; use :func:`field_fixup` hook instead.
    """

    def decorator(func: Callable):
        return _make_field_processor(func, _hooks.HookType.FIELD_POSTPROCESSOR, field_names)

    return decorator


@export
def after_field_set(*field_names: str):
    """Decorate method to be executed after any of given fields (or all, if no
    name was provided) is set or updated in the model with a successfully
    parsed value.

    This hook can be used to set derived field(-s) in the model, e.g. to also
    set ``modified`` when ``created`` is set. However, if field is set to an
    incorrect value, this hook will not be called.

    The decorated method can be defined with no arguments, or with any
    subsequence of the following arguments:

    **cls**
        The current model type.

    **self**
        The current model object.

    **loc**
        The location in the model.

        Useful to check which field is currently being set when hook is meant
        to be used for several fields.

    **value**
        The final value of a field set.

        This will be the output of type parser for a current field, or a last
        field postprocessor (if any).

    .. versionadded:: 0.36.0
    """

    def decorator(func):
        supported_param_names = ("cls", "self", "loc", "value")
        proxy = _compile_proxy(func, supported_param_names)
        hook = cast(_hooks.FieldHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_type__ = _hooks.HookType.FIELD_FIXUP
        hook.__modelity_hook_field_names__ = set(field_names)
        return hook

    return decorator


@export
def model_fixup():
    """Decorate model's method as a model-level fixup function.

    Fixup hooks can be run for a given model using
    :func:`modelity.helpers.fixup` helper. This functionality can be used to
    perform some user-defined updates in the model tree before validation takes
    place and only after successful parsing. Fixup hooks can be fed with
    user-defined context object, and therefore it is possible to pass external
    data to set in the model before validation takes place.

    The decorated method can be defined with no arguments, or with any
    subsequence of the following arguments:

    **cls**
        The current model type.

    **self**
        The current model object.

    **root**
        The root model.

        This is the one for which :func:`modelity.helpers.fixup` was originally
        called.

    **ctx**
        The user-defined fixup context.

        This can be used to pass some external data (e.g. API call results) to
        the model and use those during fixup. The type and structure is
        completely up to the user, Modelity will simply pass this to the
        user-defined fixup hooks and will not perform any additional checks.

    **loc**
        The location in the model tree.

        Will be empty for root model, or non-empty for nested one.

    .. versionchanged:: 0.37.0

        * Now these hooks can only be called on demand via
          :func:`modelity.helpers.fixup` helper or dedicated visitor.
        * Added *root* and *ctx* arguments.

    .. versionadded:: 0.36.0
    """

    def decorator(func):
        supported_param_names = ("cls", "self", "root", "ctx", "loc")
        proxy = _compile_proxy(func, supported_param_names)
        hook = cast(_hooks.ModelHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_type__ = _hooks.HookType.MODEL_FIXUP
        return hook

    return decorator


@export
def model_prevalidator():
    """Decorate model's method as a model-level prevalidation hook.

    Model prevalidators are executed as the initial validation step, before any
    other validators, including built-in ones.

    Model prevalidators can be used to skip other validators for the current
    model. This feature can be used either conditionally disable validation, or
    to replace it with custom one. To skip other validators, ``True`` must be
    returned. Returning ``True`` only applies to the instances of the model
    where model prevalidator returning ``True`` is defined.

    .. important::
        Returning ``True`` and skipping other validators also applies to
        built-in ones. For example, required fields validation will also be
        skipped if ``True`` is returned.

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
    """

    def decorator(func):
        return _make_model_validator(func, _hooks.HookType.MODEL_PREVALIDATOR)

    return decorator


@export
def model_postvalidator():
    """Decorate model's method as a model-level postvalidation hook.

    Model postvalidators are executed as the final validation step, after model
    prevalidators, built-in validators and field-level validators.

    The arguments for the decorated method are exactly the same as for
    :func:`model_prevalidator` hook.
    """

    def decorator(func):
        return _make_model_validator(func, _hooks.HookType.MODEL_POSTVALIDATOR)

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
    """

    def decorator(func):
        supported_param_names = ("cls", "self", "root", "ctx", "errors", "loc", "value")
        proxy = _compile_proxy(func, supported_param_names)
        hook = cast(_hooks.FieldHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_type__ = _hooks.HookType.FIELD_VALIDATOR
        hook.__modelity_hook_field_names__ = set(field_names)
        return hook

    return decorator


@export
def location_validator(*patterns: str):
    """Decorate model's method as a location validator.

    This validator is meant to be used when model validation requires access to
    nested models, collections of models etc. It runs for every value that is
    set in the model and its location suffix matches given pattern, which also
    supports wildcards via ``*`` (star) character.

    For example:

    .. testcode::

        from modelity.api import Model, location_validator, validate

        class Dummy(Model):

            class Nested(Model):
                foo: int

            nested: Nested

            @location_validator("nested.foo")  # This is matched to location's suffix
            def _validate_nested_foo(loc, value):
                if value < 0:
                    raise ValueError(f"value at {loc} must be >= 0")

    .. doctest::

        >>> dummy = Dummy(nested=Dummy.Nested(foo=-1))
        >>> validate(dummy)
        Traceback (most recent call last):
          ...
        modelity.exc.ValidationError: Found 1 validation error for model 'Dummy':
          nested.foo:
            value at nested.foo must be >= 0 [code=modelity.EXCEPTION, exc_type=ValueError]

    Thanks to this validator it is now possible to define entire validation
    logic for a model in one place without affecting nested models which may
    have different constraints if are used in another parent model.

    Following arguments can be used in decorated function:

    **cls**
        The model type.

        This is the type this decorator is declared in.

    **self**
        The instance of *cls* for which this decorator runs.

    **root**
        The root model instance.

        If different than *self* then this validator runs for a nested model.

    **ctx**
        The user-defined validation context.

        Check :ref:`guide-validation-using_context` for more details.

    **errors**
        Mutable list of errors.

        Can be extended by this hook to signal validation errors.
        Alternatively, :exc:`ValueError` exception can be raised and will
        automatically be converted into error and added to this list.

    **loc**
        The location of the currently validated value.

        This validator runs if and only if the suffix of this location matches
        one of patterns defined.

    **value**
        The validated value.

    .. versionadded:: 0.27.0

    :param `*patterns`:
        Location patterns to run this validator for.

        These are relative to the model where this decorator was used, so first
        element in each pattern refers to model's fields, second (if any) to
        nested models or collection items etc.

        Following wildcards are supported:

        * ``?`` - matches exactly one location element (e.g. ``foo.?.bar`` will match ``foo.0.bar``, but not ``foo.0.0.bar``)
        * ``*`` - matches one or more location elements (e.g. ``foo.*.baz`` will match ``foo.bar.0.baz``, but not ``foo.baz``)
        * ``**`` - matches zero or more location elements (e.g. ``foo.**.baz`` will match both ``foo.bar.0.baz`` and ``foo.baz``)
    """

    def decorator(func):
        supported_param_names = ("cls", "self", "root", "ctx", "errors", "loc", "value")
        proxy = _compile_proxy(func, supported_param_names)
        hook = cast(_hooks.LocationHook, proxy)
        hook.__modelity_hook_id__ = _utils.next_unique_id()
        hook.__modelity_hook_type__ = _hooks.HookType.LOCATION_VALIDATOR
        hook.__modelity_hook_patterns__ = set(
            Pattern(*[_utils.to_int_or_str(p) for p in x.split(".")]) for x in patterns
        )
        if not hook.__modelity_hook_patterns__:
            hook.__modelity_hook_patterns__ = {Pattern("**")}
        return hook

    return decorator


def _make_field_processor(func: Callable, hook_type: _hooks.HookType, field_names: tuple) -> _hooks.FieldHook:
    supported_param_names = ("cls", "errors", "loc", "value")
    proxy = _compile_proxy(func, supported_param_names)
    hook = cast(_hooks.FieldHook, proxy)
    hook.__modelity_hook_id__ = _utils.next_unique_id()
    hook.__modelity_hook_type__ = hook_type
    hook.__modelity_hook_field_names__ = set(field_names)
    return hook


def _make_model_validator(func: Callable, hook_type: _hooks.HookType) -> _hooks.ModelHook:
    supported_param_names = ("cls", "self", "root", "ctx", "errors", "loc")
    proxy = _compile_proxy(func, supported_param_names)
    hook = cast(_hooks.ModelHook, proxy)
    hook.__modelity_hook_id__ = _utils.next_unique_id()
    hook.__modelity_hook_type__ = hook_type
    return hook


def _compile_proxy(
    func: Callable,
    supported_param_names: Sequence[str],
) -> Callable:
    given_param_names = _utils.extract_given_param_names_subsequence(func, supported_param_names)
    func_params = []
    for name in supported_param_names:
        if name in given_param_names:
            func_params.append(f"{name}={name}")
    hook_code = textwrap.dedent(
        f"""
    @functools.wraps(func)
    def proxy({', '.join(supported_param_names)}):
        return func({', '.join(func_params)})
    """
    )
    l: dict[str, Any] = {}
    g = dict(globals())
    g["func"] = func
    exec(hook_code, g, l)
    return cast(Callable, l["proxy"])
