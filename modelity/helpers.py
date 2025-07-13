from typing import Any, Callable, Optional, cast

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
    output = {}
    visitor = DefaultDumpVisitor(output)
    if exclude_unset:
        visitor = cast(IModelVisitor, ConstantExcludingModelVisitorProxy(visitor, Unset))
    if exclude_none:
        visitor = cast(IModelVisitor, ConstantExcludingModelVisitorProxy(visitor, None))
    if exclude_if is not None:
        visitor = cast(IModelVisitor, ConditionalExcludingModelVisitorProxy(visitor, exclude_if))
    model.accept(visitor)
    return output


def validate(model: IModel, ctx: Any=None):
    errors = []
    visitor = DefaultValidateVisitor(model, errors, ctx)
    model.accept(visitor)
    if errors:
        raise ValidationError(model, tuple(errors))
