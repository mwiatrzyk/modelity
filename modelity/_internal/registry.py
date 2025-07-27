import functools
from typing import Any, Callable, Optional, get_origin

from modelity import _utils
from modelity.exc import UnsupportedTypeError
from modelity.interface import ITypeDescriptor, ITypeDescriptorFactory


class TypeDescriptorFactoryRegistry:

    def __init__(self):
        self._registered_type_descriptors = {}

    def _wrap_type_descriptor_factory(self, func) -> Callable:

        @functools.wraps(func)
        def proxy(typ: Any, make_type_descriptor: ITypeDescriptorFactory, type_opts: Optional[dict]) -> ITypeDescriptor:
            kw: dict[str, Any] = {}
            if "typ" in given_param_names:
                kw["typ"] = typ
            if "make_type_descriptor" in given_param_names:
                kw["make_type_descriptor"] = make_type_descriptor
            if "type_opts" in given_param_names:
                kw["type_opts"] = type_opts
            return func(**kw)

        supported_param_names = ("typ", "make_type_descriptor", "type_opts")
        given_param_names = _utils.extract_given_param_names_subsequence(func, supported_param_names)
        return proxy

    def attach(self, other: "TypeDescriptorFactoryRegistry"):
        self._registered_type_descriptors.update(other._registered_type_descriptors)

    def type_descriptor_factory(self, typ: Any):

        def decorator(func):
            return self.register_type_descriptor_factory(typ, func)

        return decorator

    def register_type_descriptor_factory(self, typ: Any, func: Callable) -> ITypeDescriptorFactory:
        proxy = self._wrap_type_descriptor_factory(func)
        self._registered_type_descriptors[typ] = proxy
        return proxy

    def make_type_descriptor(self, typ: Any, type_opts: Optional[dict] = None) -> ITypeDescriptor:
        def call_factory(factory: Callable) -> ITypeDescriptor:
            return factory(typ, self.make_type_descriptor, type_opts)

        factory = self._registered_type_descriptors.get(typ)
        if factory is None:
            origin = get_origin(typ)
            factory = self._registered_type_descriptors.get(origin)
        if factory is not None:
            return call_factory(factory)
        if isinstance(typ, type):
            for cls in typ.mro():
                factory = self._registered_type_descriptors.get(cls)
                if factory is not None:
                    return call_factory(factory)
        custom_type_descriptor_maker = getattr(typ, "__modelity_type_descriptor__", None)
        if custom_type_descriptor_maker is not None and callable(custom_type_descriptor_maker):
            return call_factory(self._wrap_type_descriptor_factory(custom_type_descriptor_maker))
        raise UnsupportedTypeError(typ)
