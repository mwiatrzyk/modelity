from typing import Any, Optional, TypeVar, overload

from modelity.interface import ITypeDescriptor

T = TypeVar("T")


@overload
def make_type_descriptor(typ: type[T], type_opts: Optional[dict] = None) -> ITypeDescriptor[T]: ...


@overload
def make_type_descriptor(typ: Any, type_opts: Optional[dict] = None) -> ITypeDescriptor: ...


def make_type_descriptor(typ: Any, type_opts: Optional[dict] = None) -> ITypeDescriptor:
    from modelity._internal.type_descriptors.all import registry

    return registry.make_type_descriptor(typ, type_opts or {})
