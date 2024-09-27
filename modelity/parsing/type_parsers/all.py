from modelity.parsing.providers import TypeParserProvider

from . import annotated, any, bool, enum, literal, model, none, numeric, string, union
from .collections import all as _collections

provider = TypeParserProvider()
provider.attach(_collections.provider)
provider.attach(annotated.provider)
provider.attach(any.provider)
provider.attach(bool.provider)
provider.attach(enum.provider)
provider.attach(literal.provider)
provider.attach(model.provider)
provider.attach(none.provider)
provider.attach(numeric.provider)
provider.attach(string.provider)
provider.attach(union.provider)
