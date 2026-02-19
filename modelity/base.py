import abc
from typing import Any, Mapping, Optional, Protocol, Sequence, Set, Union

from modelity import _export_list

from .loc import Loc
from .error import Error
from .unset import UnsetType
from .model import Model  # TODO: Move to here

__all__ = export = _export_list.ExportList()  # type: ignore


@export
class TypeHandler(abc.ABC):
    """Base class for type handlers.

    Type handlers are used by Modelity to provide type-specific runtime logic
    to models. Type handlers are constructed from type object or type
    annotations when model type is created and then used by model instances to
    handle user data.

    .. versionadded:: 0.36.0
        Replaced ``modelity.interface.ITypeDescriptor`` used earlier.
    """

    @abc.abstractmethod
    def parse(self, errors: list[Error], loc: Loc, value: Any, /) -> Union[Any, UnsetType]:
        """Parse given value as instance of handled type.

        Successful parsing must return instance of handled type, which can be
        unchanged *value* if it already has desired type.

        Failure must be reported by one or more errors added to *errors* list,
        and :obj:`modelity.unset.Unset` value returned.

        :param errors:
            Mutable list of errors.

        :param loc:
            The current location in the model.

        :param value:
            The input value.
        """

    @abc.abstractmethod
    def accept(self, visitor: "ModelVisitor", loc: Loc, value: Any, /):
        """Accept given model visitor.

        This method is meant to provide visitor accepting logic for handled
        type. Basically, this method will call the most adequate visitor
        method, or (for complex types) sequence of visitor methods. See
        :class:`ModelVisitor` for more details.

        :param visitor:
            The visitor to accept.

        :param loc:
            The visited location in the model.

        :param value:
            The value to process.

            It can be assumed that this value has the right type already.
        """


@export
class TypeHandlerFactory(Protocol):
    """Protocol describing type handler factories.

    .. versionadded::
        Replaced ``modelity.interface.ITypeDescriptorFactory`` used earlier.
    """

    def __call__(self, typ: Any, /, **type_opts) -> TypeHandler:
        """Create a type handler for the provided type and options.

        :param typ:
            The type or special form to create a handler for.

        :param type_opts:
            Optional type-specific options passed to the handler.
        """
        ...


@export
class SupportsValidate(abc.ABC):
    """Base class for types that support validation."""

    @abc.abstractmethod
    def validate(self, errors: list[Error], loc: Loc, value: Any) -> bool:
        """Validate the value.

        Returns True if the value is valid without modifying the errors list.
        Returns False if the value is invalid and adds one or more errors to
        the errors list.

        :param errors:
            Mutable list of errors.

        :param loc:
            The current location in the model.

        :param value:
            The validated value.
        """


@export
class Constraint(SupportsValidate):
    """Base class for constraints.

    Constraints are used to define parsing- and validation-time criteria that
    must be met for successful parsing/validation. Instances of this base class
    are used with types wrapped with :obj:`typing.Annotated`.

    .. versionadded:: 0.36.0
        Replaced ``modelity.interface.IConstraint`` used earlier.
    """


@export
class TypeHandlerWithValidation(TypeHandler, SupportsValidate):
    """Base class for type handlers that need to run additional type-specific
    validation when model is validated.

    For example, this base class is used by type handler for
    :obj:`typing.Annotated` types to ensure that constraints are still
    satisfied when model is validated, which is impossible to ensure only
    during parsing stage for mutable types.

    .. versionadded:: 0.36.0
        Replaced ``modelity.interface.IValidatableTypeDescriptor`` used earlier.
    """


@export
class ModelVisitor(abc.ABC):
    """Base class for model data visitors.

    This mechanism allows to traverse through Modelity models in a
    deterministic way and, depending on the implementation, serialize or
    validate it.

    .. versionadded:: 0.36.0
        Replaced ``modelity.interface.IModelVisitor`` used earlier.
    """

    @abc.abstractmethod
    def visit_model_begin(self, loc: Loc, value: "Model") -> Optional[bool]:  # TODO: use sentinel
        """Start visiting model object.

        :param loc:
            The location of the visited model.

        :param value:
            The visited model object.
        """
        ...

    @abc.abstractmethod
    def visit_model_end(self, loc: Loc, value: "Model"):
        """Finish visiting model object.

        :param loc:
            The location of the visited model.

        :param value:
            The visited model object.
        """
        ...

    @abc.abstractmethod
    def visit_model_field_begin(self, loc: Loc, value: Any, field: "Field") -> Optional[bool]:  # TODO: use sentinel
        """Start visiting model field.

        This is called for every field in a model no matter if the field is set
        or not.

        :param loc:
            The location of the visited value.

        :param value:
            The visited field value.

        :param field:
            The visited field metadata.
        """
        ...

    @abc.abstractmethod
    def visit_model_field_end(self, loc: Loc, value: Any, field: "Field"):
        """Finish visiting model field.

        :param loc:
            The location of the visited value.

        :param value:
            The visited field value.

        :param field:
            The visited field metadata.
        """
        ...

    @abc.abstractmethod
    def visit_mapping_begin(self, loc: Loc, value: Mapping) -> Optional[bool]:  # TODO: use sentinel
        """Start visiting a mapping object.

        :param loc:
            The location of the visited mapping object.

        :param value:
            The visited mapping object.
        """
        ...

    @abc.abstractmethod
    def visit_mapping_end(self, loc: Loc, value: Mapping):
        """Finish visiting a mapping object.

        :param loc:
            The location of the visited mapping object.

        :param value:
            The visited mapping object.
        """
        ...

    @abc.abstractmethod
    def visit_sequence_begin(self, loc: Loc, value: Sequence) -> Optional[bool]:  # TODO: use sentinel
        """Start visiting a sequence object.

        :param loc:
            The location of the visited sequence object.

        :param value:
            The visited sequence object.
        """
        ...

    @abc.abstractmethod
    def visit_sequence_end(self, loc: Loc, value: Sequence):
        """Finish visiting a sequence object.

        :param loc:
            The location of the visited sequence object.

        :param value:
            The visited sequence object.
        """
        ...

    @abc.abstractmethod
    def visit_set_begin(self, loc: Loc, value: Set) -> Optional[bool]:  # TODO: use sentinel
        """Start visiting a set object.

        :param loc:
            The location of the visited set object.

        :param value:
            The visited set object.
        """
        ...

    @abc.abstractmethod
    def visit_set_end(self, loc: Loc, value: Set):
        """Finish visiting a set object.

        :param loc:
            The location of the visited set object.

        :param value:
            The visited set object.
        """
        ...

    @abc.abstractmethod
    def visit_none(self, loc: Loc, value: None):
        """Visit a ``None`` value.

        Called when :obj:`None` object is found.

        :param loc:
            The location of the visited value.

        :param value:
            The visited value.
        """
        ...

    @abc.abstractmethod
    def visit_unset(self, loc: Loc, value: UnsetType):
        """Visit an ``Unset`` value.

        Called when :obj:`modelity.unset.Unset` object is found.

        :param loc:
            The location of the visited value.

        :param value:
            The visited value.
        """
        ...

    @abc.abstractmethod
    def visit_scalar(self, loc: Loc, value: Any):
        """Visit scalar object.

        Scalars are primitive objects that are neither containers, nor model
        objects. All Python primitive types (ints, floats, strings, booleans,
        enums, datetimes etc.) are scalars from the Modelity point of view.

        :param loc:
            The location of the visited value.

        :param value:
            The visited value.
        """
        ...

    @abc.abstractmethod
    def visit_any(self, loc: Loc, value: Any):
        """Visit any value.

        This is called for values from untyped containers, fields marked with
        :obj:`typing.Any` or typed containers where :obj:`typing.Any` is used
        as a type hint.

        This method, unlike :meth:`visit_scalar`, can also be called with
        elements that are containers, not scalars.

        Implementations are responsible for deciding whether to recurse into
        the value if it is a container.

        :param loc:
            The location of the visited value.

        :param value:
            The visited value.
        """
        ...


class Field:  # TODO: move `model.Field` here
    pass


# class Model:  # TODO: move `model.Model` here
#     pass
