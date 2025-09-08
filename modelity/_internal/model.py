from typing import Any, Optional

from modelity.interface import ITypeDescriptor


def make_type_descriptor(typ: Any, type_opts: Optional[dict] = None) -> ITypeDescriptor:
    """Make type descriptor for provided type and type options.

    If no descriptor could be created, then
    :exc:`modelity.exc.UnsupportedTypeError` will be thrown.

    This function is executed by model metaclass when model type is created,
    and later each model instance simply reuses type descriptors created by
    metaclass.

    :param typ:
        The type to create descriptor for.

    :param type_opts:
        The dict containing type options.

        For example, things like date/time format will be defined here.
    """
    from modelity._internal.type_descriptors.all import registry

    return registry.make_type_descriptor(typ, type_opts or {})
