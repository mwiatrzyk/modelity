from typing_extensions import TypeGuard

from modelity import _utils

__all__ = export = _utils.ExportList(["Unset"])  # type: ignore


@export
class UnsetType:
    """Singleton type for representing unset or undefined values.

    It has only one global instance to allow fast is-a tests in the code and
    always evaluates to ``False``.
    """

    __slots__: list = []

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "Unset"

    def __bool__(self):
        return False


@export
def is_unset(obj: object) -> TypeGuard[UnsetType]:
    """Check if *obj* is instance of :class:`UnsetType` type.

    .. versionadded:: 0.17.0
    """
    return obj is Unset


#: Singleton instance of the UnsetType.
Unset = UnsetType()
