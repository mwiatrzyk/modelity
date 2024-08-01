from modelity.parsing.registry import TypeParserRegistry

from . import bool, none, numeric, string, union

registry = TypeParserRegistry()
registry.attach(bool.registry)
registry.attach(none.registry)
registry.attach(numeric.registry)
registry.attach(string.registry)
registry.attach(union.registry)
