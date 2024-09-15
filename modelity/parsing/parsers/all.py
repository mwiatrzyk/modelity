from modelity.parsing.registry import TypeParserRegistry

from . import annotated, any, bool, enum, literal, model, none, numeric, string, union
from .collections import all as _collections

registry = TypeParserRegistry()
registry.attach(_collections.registry)
registry.attach(annotated.registry)
registry.attach(any.registry)
registry.attach(bool.registry)
registry.attach(enum.registry)
registry.attach(literal.registry)
registry.attach(model.registry)
registry.attach(none.registry)
registry.attach(numeric.registry)
registry.attach(string.registry)
registry.attach(union.registry)
