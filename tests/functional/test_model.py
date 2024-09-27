from typing import Optional, Type

import pytest

from modelity.model import Model
from modelity.parsing.type_parsers import all


class Base(Model):

    class Config:
        parser_registry = all.provider


class Dummy(Base):
    foo: int
    bar: Optional[float]
    baz: Optional[str]


def test_create_model_with_no_initialization():
    model = Dummy()
    model.foo = "123"
    # assert model.foo == 123
