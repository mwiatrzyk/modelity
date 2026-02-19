"""Module providing ``__all__`` list automation helper.

.. versionadded::
    Functionality moved from ``_utils.py`` to remove circular imports and need
    of inline importing.
"""

from typing import TypeVar

T = TypeVar("T")


class ExportList(list):
    """Helper for making ``__all__`` lists automatically by decorating public
    names."""

    def __call__(self, type_or_func: T) -> T:
        name = getattr(type_or_func, "__name__", None)
        if name is None:
            raise TypeError(f"cannot export {type_or_func!r}; the '__name__' property is undefined")
        self.append(name)
        return type_or_func
