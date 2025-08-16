from typing import Any, Callable, Generic, Optional, TypeVar, cast

from modelity import _utils
from modelity.error import Error
from modelity.exc import ValidationError
from modelity.interface import IModelVisitor
from modelity.loc import Loc
from modelity.model import Model
from modelity.unset import Unset
from modelity.visitors import (
    ConditionalExcludingModelVisitorProxy,
    ConstantExcludingModelVisitorProxy,
    DefaultDumpVisitor,
    DefaultValidateVisitor,
)

__all__ = export = _utils.ExportList()  # type: ignore

MT = TypeVar("MT", bound=Model)


@export
def has_fields_set(model: Model) -> bool:
    """Check if *model* has at least one field set.

    :param model:
        The model object.
    """
    return next(iter(model), None) is not None


@export
def dump(
    model: Model,
    exclude_unset: bool = False,
    exclude_none: bool = False,
    exclude_if: Optional[Callable[[Loc, Any], bool]] = None,
) -> dict:
    """Serialize given model to a dict.

    This helper is designed to handle most common dump scenarios, like skipping
    unset fields or optional field set to ``None``. More advanced behavior can
    be achieved by implementing custom
    :class:`modelity.interface.IModelVisitor` interface and running
    :meth:`modelity.model.Model.accept` method directly.

    :param model:
        The model to serialize.

    :param exclude_unset:
        Exclude unset fields.

    :param exclude_none:
        Exclude fields set to ``None``.

    :param exclude_if:
        Conditional function executed for every model location and value.

        Should return ``True`` to drop the value from resulting dict, or
        ``False`` to leave it. Can be used to achieve exclusion based on
        location and/or value.
    """
    output: dict = {}
    visitor: IModelVisitor = DefaultDumpVisitor(output)
    if exclude_unset:
        visitor = cast(IModelVisitor, ConstantExcludingModelVisitorProxy(visitor, Unset))
    if exclude_none:
        visitor = cast(IModelVisitor, ConstantExcludingModelVisitorProxy(visitor, None))
    if exclude_if is not None:
        visitor = cast(IModelVisitor, ConditionalExcludingModelVisitorProxy(visitor, exclude_if))
    model.accept(visitor, Loc())
    return output


@export
def load(model_type: type[MT], data: dict, ctx: Any = None) -> MT:
    """Parse and validate given raw data using provided model type.

    This is a helper function meant to be used to create models from data that
    is coming from an untrusted source, like API request, JSON file etc.

    On success, this function returns new instance of the given *model_type*.

    On failure, this function raises :exc:`modelity.exc.ModelError`.

    Here's an example:

    .. testcode::

        from modelity.model import Model
        from modelity.helpers import load

        class Example(Model):
            foo: int
            bar: int

    .. doctest::

        >>> untrusted_data = {"foo": "123", "bar": "456"}
        >>> example = load(Example, untrusted_data)
        >>> example
        Example(foo=123, bar=456)

    :param model_type:
        The model type to parse data with.

    :param data:
        The data to be parsed.

    :param ctx:
        The user-defined validation context.
    """
    obj = model_type(**data)
    validate(obj, ctx=ctx)
    return obj


@export
def validate(model: Model, ctx: Any = None):
    """Validate provided model.

    On success, this method raises no exception and returns ``None``.

    On failure, :exc:`modelity.exc.ValidationError` exception is raised.

    :param model:
        The model to validate.

    :param ctx:
        The user-defined validation context.
    """
    errors: list[Error] = []
    visitor = DefaultValidateVisitor(model, errors, ctx)
    model.accept(visitor, Loc())
    if errors:
        raise ValidationError(model, tuple(errors))


@export
class ModelLoader(Generic[MT]):
    """Similar to :func:`load` function, but allows to create loader for given
    model type and then create instances of that model using keyword args.

    Example use:

    .. testcode::

        from modelity.model import Model
        from modelity.helpers import ModelLoader

        class Dummy(Model):
            a: int
            b: str

        DummyLoader = ModelLoader(Dummy)

    .. doctest::

        >>> one = DummyLoader(a=1, b="spam")
        >>> one
        Dummy(a=1, b='spam')

    .. versionadded:: 0.17.0

    :param model_type:
        The model type.

    :param ctx:
        The user-defined validation context.
    """

    def __init__(self, model_type: type[MT], ctx: Any = None):
        self._model_type = model_type
        self._ctx = ctx

    def __call__(self, **kwargs) -> MT:
        """Create and validate instance of the given model type.

        On success, valid model instance is returned.

        On failure, :exc:`modelity.exc.ModelError` exception is raised.

        :param `**kwargs`:
            Named arguments for model's constructor.
        """
        return load(self._model_type, kwargs, self._ctx)
