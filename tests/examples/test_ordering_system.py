import datetime
from typing import Annotated, Optional

import pytest

from modelity.api import (
    Model,
    Gt,
    UserError,
    ValidationError,
    fixup,
    validate,
    field_fixup,
    model_fixup,
    field_validator,
    field_postprocessor
)


class OrderItem(Model):
    name: str
    quantity: Annotated[int, Gt(0)]
    price: Annotated[float, Gt(0)]

    # -- field-scoped postprocessing

    @field_postprocessor("name")
    def _strip(cls, value: str):
        return value.strip()

    @property
    def total_price(self) -> float:
        return self.quantity * self.price


class Order(Model):
    items: list[OrderItem]
    total: Optional[float] = None
    modified: Optional[datetime.datetime] = None
    created: Optional[datetime.datetime] = None

    # -- construction or modification fixup hooks

    @field_fixup("items")
    def _update_total(self):
        self.total = sum(x.total_price for x in self.items)

    # -- construction fixup hooks

    @model_fixup()
    def _update_timestamps(self):
        now = datetime.datetime.now()
        self.modified = now
        if self.created is None:
            self.created = now

    # -- validation hooks

    @field_validator("total")
    def _verify_total(self):
        if self.total != sum(x.total_price for x in self.items):
            raise UserError(msg="incorrect total price", code="PRICE_CHECK_ERROR")


@pytest.fixture
def sut():
    return Order(items=[
        OrderItem(name="apple", quantity=2, price=3.0),
        OrderItem(name="banana", quantity=1, price=2.0),
    ])


def test_total_is_computed_and_assigned_automatically_on_initialization(sut: Order):
    assert sut.total == 8.0


def test_created_and_modified_are_computed_and_assigned_automatically_on_initialization(sut: Order):
    fixup(sut)
    assert sut.modified is not None
    assert sut.created == sut.modified


def test_validation_fails_after_modifying_order_list_without_fixup(sut: Order):
    sut.items.append(OrderItem(name="oranges", quantity=4, price=1.5))
    with pytest.raises(ValidationError):
        validate(sut)


def test_validation_passes_after_modifying_order_list_and_calling_fixup_before_validate(sut: Order):
    sut.items.append(OrderItem(name="oranges", quantity=4, price=1.5))
    fixup(sut)
    validate(sut)
