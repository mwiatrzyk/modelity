.. _quickstart:

Quickstart
==========

Installation
------------

Modelity is available on PyPI and can be installed or added to your
project's dependencies using any available Python package manager.

For example, to install Modelity using **pip**, run following command::

    $ pip install modelity

Defining domain models
----------------------

For the purpose of this quickstart guide we'll create a domain model of a
simple ordering system composed of two models: **OrderItem** (representing
single order item) and **Order** (representing collection of order items).
Let's create initial draft of these two models using Modelity:

.. testcode:: foo

    import datetime

    from modelity.api import Model

    class OrderItem(Model):
        name: str
        quantity: int
        price: float

    class Order(Model):
        items: list[OrderItem]
        modified: datetime.datetime
        created: datetime.datetime

All fields in models created above are currently **required** and have their
types set, but with no constraints yet. Let's now add some field-level
constraints and to do so we need :obj:`typing.Annotated` and some constraints
provided by Modelity. Here's an updated previous example with comments:

.. testcode::

    import datetime
    from typing import Annotated

    from modelity.api import Model, Gt, Ge, MinLen

    class OrderItem(Model):
        name: str
        quantity: Annotated[int, Gt(0)]  # quantity must be > 0
        price: Annotated[float, Ge(0)]  # price must be >= 0 (we can offer things for free)

    class Order(Model):
        items: Annotated[list[OrderItem], MinLen(1)]  # minimum number of items in order is 1
        modified: datetime.datetime
        created: datetime.datetime

.. note::

    Constraints to be used with :obj:`typing.Annotated` are used to ensure data
    integrity at the field level. Check :mod:`modelity.constraints` to get
    documentation on all supported constraints.

Now we have field-level constraint set, so each field will be prevented from
being set to either wrong type, or right type but incorrect value (e.g.
negative price). But none of these fields have any knowledge about the model
itself and neighboring dependent fields. For example, how to ensure that
``modified >= created``? To do so we need to define **cross-field invariants**
and here Modelity hook system comes in:

.. testcode::

    import datetime
    from typing import Annotated

    from modelity.api import Model, UserError, Gt, Ge, MinLen, field_validator

    class OrderItem(Model):
        name: str
        quantity: Annotated[int, Gt(0)]
        price: Annotated[float, Ge(0)]

    class Order(Model):
        items: Annotated[list[OrderItem], MinLen(1)]
        modified: datetime.datetime
        created: datetime.datetime

        @field_validator("modified")
        def _validate_modified(self, value: datetime.datetime):
            if value < self.created:
                raise UserError(f"Incorrect value for `modified` field; cannot precede `created` datetime")

We've used :func:`modelity.api.field_validator` hook to create field-level
validators for ``modified`` field. This hook will run during model validation
and only if ``modified`` field is set.

.. important::
   The :exc:`modelity.api.UserError` exception is in fact a helper. It will not
   be propagated, but handled by Modelity, converted into
   :class:`modelity.api.Error` object and added to validation errors list.
   We'll talk about error handling in more details later in this handbook.

Now the model is basically complete, but it still can be improved a bit.
Currently, both ``modified`` and ``created`` have to be explicitly given during
construction of the model. Let's make ``created`` to be automatically assigned
during construction to a current datetime, and ``modified`` to automatically be
aligned with ``created``. We can achieve that by specifying **default value**
for ``created`` field and by using :func:`modelity.hooks.after_field_set` hook:

.. testcode::

    import datetime
    from typing import Annotated

    from modelity.api import (
        Model, field_info, is_unset, UserError, Deferred, Gt, Ge, MinLen,
        Unset, field_validator, after_field_set
    )

    class OrderItem(Model):
        name: str
        quantity: Annotated[int, Gt(0)]
        price: Annotated[float, Ge(0)]

    class Order(Model):
        items: Annotated[list[OrderItem], MinLen(1)]  # This is the only field that is required
        modified: Deferred[datetime.datetime] = Unset  # Deferred[T] -> can be omitted when constructing, but must be set before validation
        created: datetime.datetime = field_info(default_factory=datetime.datetime.now)  # current datetime will be used as default

        @after_field_set("created")
        def _update_modified(self, value: datetime.datetime):
            if is_unset(self.modified):
                self.modified = value  # Set `modified` to `created` if not set yet

        @field_validator("modified")
        def _validate_modified(self, value: datetime.datetime):
            if value < self.created:
                raise UserError(f"Incorrect value for `modified` field; cannot precede `created` datetime")

At this point our domain model is complete and we're ready to move forward.

Creating model instances
------------------------

Creating model instances is done by calling model's constructor and passing
field values using keyword args:

.. doctest::

    >>> order = Order(items=[OrderItem(name="apple", quantity=2, price=2.5)])
    >>> order.created is not None
    True
    >>> order.created == order.modified
    True

As you can see, also ``created`` and ``modified`` were implicitly set. Of
course it is possible to give all the arguments by hand:

.. doctest::

    >>> import datetime
    >>> apple = OrderItem(name="apple", quantity=2, price=2.5)
    >>> order = Order(
    ...     items=[apple],
    ...     modified=datetime.datetime(2026, 1, 2),
    ...     created=datetime.datetime(2026, 1, 1),
    ... )
    >>> order.items
    [OrderItem(name='apple', quantity=2, price=2.5)]
    >>> order.created
    datetime.datetime(2026, 1, 1, 0, 0)
    >>> order.modified
    datetime.datetime(2026, 1, 2, 0, 0)

If constructor is called without arguments and model has required fields
defined then you'll get a :exc:`modelity.api.ParsingError` exception with
detailed list of errors, in this case signalling which required fields were
found missing:

.. doctest::

    >>> Order()
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Order':
      items:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]

Similar error will also be reported when you try to use an incompatible value
for a field:

.. doctest::

    >>> Order(items=[apple], created=123)
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Order':
      created:
        Not a valid value; expected: datetime [code=modelity.INVALID_TYPE, value_type=int, expected_types=[datetime], allowed_types=[str]]

But even string can be accepted (or any other compatible type) for as long as
Modelity parsing engine can automatically convert it to a valid type, like in
example below:

.. doctest::

    >>> banana = OrderItem(name="banana", quantity="3", price="1.5")
    >>> type(banana.quantity)
    <class 'int'>
    >>> type(banana.price)
    <class 'float'>
    >>> banana
    OrderItem(name='banana', quantity=3, price=1.5)

Modifying existing model instances
----------------------------------

Modelity allows to alter models after creation and when doing so same mechanics
come into play as used during construction.

Let's once again create order model:

.. doctest::

    >>> apple = OrderItem(name="apple", quantity=2, price=2.5)
    >>> banana = OrderItem(name="banana", quantity=3, price=1.5)
    >>> order = Order(items=[apple, banana], created=datetime.datetime(2000, 1, 1, 0, 0))

And now let's assume that our application needs to add an *orange* to that
order. This is actually pretty straightforward; just **append** new item to the
``items`` list:

.. doctest::

    >>> orange = OrderItem(name="orange", quantity=1, price=3.0)
    >>> order.items.append(orange)

What is important, proper handling of mutable typed containers is one of core
features of Modelity, so standard type checking and coercion attempts take
place while modifying a typed container. For example, you'll not be able to
append integer number as another order item:

.. doctest::

    >>> order.items.append(123)
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'list[OrderItem]':
      3:
        Not a valid value; expected: OrderItem [code=modelity.INVALID_TYPE, value_type=int, expected_types=[OrderItem], allowed_types=[Mapping]]

Same thing will happen with model fields; you can modify those, but
modification will fail if incorrect value is provided, or provided value does
not meet field-level constraints:

.. doctest::

    >>> order.items = []
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Order':
      items:
        Expected length >= 1 [code=modelity.INVALID_LENGTH, value_type=MutableSequenceProxy, min_length=1]


Validating model instances
--------------------------

To validate models you need a :func:`modelity.api.validate` helper. It will
call all built-in validators and user-defined ones. The model is valid if
running validation succeeds without raising exceptions. For example, our
previous model is already valid:

.. doctest::

    >>> from modelity.api import validate
    >>> validate(order)

And now let's break it by setting ``modified`` datetime to be earlier than
``created`` and see what will happen if we validate again:

.. doctest::

    >>> order.modified = order.created - datetime.timedelta(days=1)
    >>> validate(order)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Order':
      modified:
        Incorrect value for `modified` field; cannot precede `created` datetime [code=modelity.USER_ERROR]

Validation errors are signalled using :exc:`modelity.exc.ValidationError`
exception.

Serializing models
------------------

To serialize models, :func:`modelity.helpers.dump` function is needed. It
serializes models to a closest JSON-compatible Python dict. This is how this
works:

.. doctest::

    >>> from modelity.helpers import dump
    >>> order.modified = order.created  # Let's fix what we broke in previous example
    >>> validate(order)  # It is recommended, yet not required
    >>> order_dict = dump(order)
    >>> order_dict
    {'items': [{'name': 'apple', 'quantity': 2, 'price': 2.5}, {'name': 'banana', 'quantity': 3, 'price': 1.5}, {'name': 'orange', 'quantity': 1, 'price': 3.0}], 'modified': '2000-01-01T00:00:00.000000', 'created': '2000-01-01T00:00:00.000000'}

Now you can use any library you like to further dump ``order_dict`` into JSON
or any other format, as this is out of Modelity scope.

Deserializing models
--------------------

To build model object from serialized data, you have to use
:func:`modelity.helpers.load` function:

.. doctest::

    >>> from modelity.helpers import load
    >>> loaded_order = load(Order, order_dict)
    >>> isinstance(loaded_order, Order)
    True
    >>> loaded_order == order
    True

This helper is automatically validating given data as it is meant to be used
with data coming from untrusted source. Therefore if you run on empty dict that
does not have required ``items`` key, following error will be reported:

.. doctest::

    >>> load(Order, {})
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Order':
      items:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]

And similar thing will happen if ``items`` exists, but is incorrect:

.. doctest::

    >>> incorrect_data = {
    ...     "items": [{"name": "banana"}]
    ... }
    >>> load(Order, incorrect_data)
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 2 parsing errors for type 'Order':
      items.0.price:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]
      items.0.quantity:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]

As seen in the examples above, each found error points to the exact location in
the input data where the error was found.

Next steps
----------

Now you've learned the basics of how Modelity can be used. You can now proceed
to the full guide to learn all features in details.
