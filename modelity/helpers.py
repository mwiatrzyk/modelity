from typing import Any, Callable, Optional, TypeVar, cast

from modelity.error import Error
from modelity.exc import ValidationError
from modelity.interface import IModel, IModelVisitor
from modelity.loc import Loc
from modelity.unset import Unset
from modelity.visitors import (
    ConditionalExcludingModelVisitorProxy,
    ConstantExcludingModelVisitorProxy,
    DefaultDumpVisitor,
    DefaultValidateVisitor,
)

MT = TypeVar("MT", bound=IModel)


def has_fields_set(model: IModel) -> bool:
    """Check if *model* has at least one field set.

    :param model:
        The model object.
    """
    return next(iter(model), None) is not None


def dump(
    model: IModel,
    exclude_unset: bool = False,
    exclude_none: bool = False,
    exclude_if: Optional[Callable[[Loc, Any], bool]] = None,
) -> dict:
    """Serialize given model to a dict.

    Underneath this helper uses :class:`modelity.visitors.DefaultDumpVisitor`
    visitor to do the heavy lifting and just orchestrates the call, building
    visitor based on arguments given.

    :param model:
        The model to serialize.

    :param exclude_unset:
        Exclude fields set to :obj:`modelity.unset.Unset` value from resulting dict.

    :param exclude_none:
        Exclude fields set to ``None`` value from resulting dict.

    :param exclude_if:
        Conditional function executed for every model location and value.

        Should return ``True`` to drop the value from resulting dict, or
        ``False`` to leave it.
    """
    output: dict = {}
    visitor: IModelVisitor = DefaultDumpVisitor(output)
    if exclude_unset:
        visitor = cast(IModelVisitor, ConstantExcludingModelVisitorProxy(visitor, Unset))
    if exclude_none:
        visitor = cast(IModelVisitor, ConstantExcludingModelVisitorProxy(visitor, None))
    if exclude_if is not None:
        visitor = cast(IModelVisitor, ConditionalExcludingModelVisitorProxy(visitor, exclude_if))
    model.accept(visitor)
    return output


def load(model_type: type[MT], data: dict, ctx: Any = None) -> MT:
    """Parse and validate given data using provided model type.

    This is a helper function meant to be used to create models from data that
    is coming from an untrusted source, like API request etc.

    On success, this function returns new instance of the given *model_type*.

    On failure, this function raises either :exc:`modelity.exc.ParsingError`
    (if it failed at parsing stage), or :exc:`modelity.model.ValidationError`
    (if it failed at model validation stage).

    Here's an example:

    .. testcode::

        from modelity.model import Model, load

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
        User-defined validation context.

        Check :meth:`Model.validate` for more information.
    """
    obj = model_type(**data)
    validate(obj, ctx=ctx)
    return obj


def validate(model: IModel, ctx: Any = None):
    errors: list[Error] = []
    visitor = DefaultValidateVisitor(model, errors, ctx)
    model.accept(visitor)
    if errors:
        raise ValidationError(model, tuple(errors))
