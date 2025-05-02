from modelity._registry import TypeDescriptorFactoryRegistry

from . import simple, special, collections, model

registry = TypeDescriptorFactoryRegistry()
registry.attach(simple.registry)
registry.attach(special.registry)
registry.attach(collections.registry)
registry.attach(model.registry)
