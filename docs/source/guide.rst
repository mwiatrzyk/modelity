User's guide
============

Declaring models
----------------

The most basic model
^^^^^^^^^^^^^^^^^^^^

The most basic model in Modelity is simply subclass of
:class:`modelity.base.Model` with no fields declared:

.. testcode::

    from modelity.base import Model

    class EmptyModel(Model):
        pass

Such declared class has no practical use as an instance, but it is perfectly
fine as a base class for other domain-specific models, especially as a place to
put application-wide filtering hooks or validators.

Required fields
^^^^^^^^^^^^^^^

All fields declared with no extra type modifiers are **required** by Modelity.
For example, this model has all fields **required**:

.. testcode::

    from modelity.base import Model

    class User(Model):
        name: str
        email: str
        age: int

All required fields must be provided by constructor when model instance is
created or otherwise the constructor will raise
:exc:`modelity.exc.ParsingError` exception:

.. doctest::

    >>> user = User()
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 3 parsing errors for type 'User':
      age:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]
      email:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]
      name:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]

And the model creation will succeed if all required fields are given:

.. doctest::

    >>> user = User(name="John Doe", email="jd@example.com", age=32)
    >>> user
    User(name='John Doe', email='jd@example.com', age=32)

The presence of required fields is additionally checked at the **validation**
phase. For example, model with ``age`` property missing will be invalid and
same error will be reported as for constructor, but just for ``age`` field
which we've just removed from the model:

.. doctest::

    >>> from modelity.helpers import validate  # This helper is used to run validation on given model
    >>> validate(user)  # The user is valid
    >>> del user.age  # We've dropped `age` property...
    >>> validate(user)  # ...and the user is no longer valid:
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'User':
      age:
        This field is required [code=modelity.REQUIRED_MISSING]

Deferred fields
^^^^^^^^^^^^^^^

.. versionadded:: 0.35.0

Modelity allows to declare fields as **deferred** which means that the field is
optional when model is being constructed, but must be provided before model is
validated. This allows to fill the model with data progressively with data, for
instance, coming from user prompts. Thanks to this mechanism you don't have to
use intermediate data structures for storing such data -- the model will handle
that for you. To declare fields as deferred use :obj:`modelity.typing.Deferred`
type modifier like in example below:

.. testcode::

    # Modelity provides an all-in-one import helper; all public names can be
    # imported from `modelity.api`.
    from modelity.api import (
        Model,
        Unset,
        Deferred,
        validate
    )

    class OrderItem(Model):
        name: Deferred[str]
        quantity: Deferred[int]
        price: Deferred[float]

Creating such declared model now becomes possible without arguments and these
fields will be assigned with special :obj:`modelity.unset.Unset` sentinel:

.. doctest::

    >>> order = OrderItem()
    >>> order
    OrderItem(name=Unset, quantity=Unset, price=Unset)

Now the model can be fed with data in steps:

.. testcode::
    :hide:

    def prompt(what):
        if what == "Enter item name":
            return "apple"
        if what == "Enter quantity":
            return 2
        if what == "Enter price":
            return 1.5

.. doctest::

    >>> order.name = prompt("Enter item name")  # user answers: apple
    >>> order
    OrderItem(name='apple', quantity=Unset, price=Unset)

Now let's try to **validate** the model. To do that we need
:func:`modelity.helpers.validate` helper function introduced earlier and call
it on our model:

.. doctest::

    >>> validate(order)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 2 validation errors for model 'OrderItem':
      price:
        This field is required [code=modelity.REQUIRED_MISSING]
      quantity:
        This field is required [code=modelity.REQUIRED_MISSING]

Validation has failed with :exc:`modelity.exc.ValidationError` as there are
still 2 deferred fields missing in the model. To make validation pass the model
has to be filled in with missing data:

.. doctest::

    >>> order.quantity = prompt("Enter quantity")  # user answers: 2
    >>> order.price = prompt("Enter price")  # user answers: 1.5
    >>> validate(order)  # will now pass

Validation stage will be described in more details in :ref:`guide_validation`
section.

Optional fields
^^^^^^^^^^^^^^^

Modelity allows to declare optional fields using any of the following type
modifiers:

===================================== ================ ==================
Modifier                              Allows ``None``? Can be left unset?
===================================== ================ ==================
:obj:`typing.Optional`                Yes              No
:obj:`modelity.typing.LooseOptional`  Yes              Yes
:obj:`modelity.typing.StrictOptional` No               Yes
===================================== ================ ==================

Since Modelity treats ``None`` as a first-class value it cannot use it to
represent the unset state of a field. Instead, a dedicated
:obj:`modelity.unset.Unset` sentinel was created and therefore handling
optionality using standard :obj:`typing.Optional` alone may be insufficient
(see the table) as it might cause false positives during typical ``if
model.field is not None`` comparisons.

And now let's take a tour around all modifiers that are used to declare fields
as **optional**.

Using ``typing.Optional[T]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Allowed values:

* objects of type ``T``
* objects of type ``U`` that can be parsed as ``T``
* ``None``

Use cases:

* non-unsettable optionals; either ``T`` or ``None``

Example:

.. testcode::

    from typing import Optional

    from modelity.api import Model, validate

    class OptionalExample(Model):
        foo: Optional[int] = None  # IMPORTANT: Optional[T] cannot be unset

.. doctest::

    >>> model = OptionalExample()
    >>> validate(model)  # OK
    >>> model.foo is None  # It was initialized with None
    True
    >>> model.foo = 123  # OK; 123 is an int
    >>> model.foo
    123
    >>> model.foo = "456"  # OK; "456" can be successfully converted to int
    >>> model.foo
    456
    >>> model.foo = None  # OK; can be set to None
    >>> model.foo is None
    True
    >>> del model.foo
    >>> model.foo  # Now this is unset
    Unset
    >>> validate(model)  # FAIL: Optional[T] cannot be unset
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'OptionalExample':
      foo:
        This field does not allow Unset; expected: Union[int, NoneType] [code=modelity.UNSET_NOT_ALLOWED, expected_type=Union[int, NoneType]]

Using ``modelity.typing.LooseOptional[T]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Allowed values:

* objects of type ``T``
* objects of type ``U`` that can be parsed as ``T``
* ``None``
* :obj:`modelity.unset.Unset`

Use cases:

* unsettable optionals; ``T``, ``None`` or ``Unset``

Example:

.. testcode::

    from modelity.api import Model, LooseOptional, validate

    class LooseOptionalExample(Model):
        foo: LooseOptional[int]

.. doctest::

    >>> model = LooseOptionalExample()
    >>> validate(model)  # OK
    >>> model.foo
    Unset
    >>> model.foo = 123  # OK
    >>> model.foo
    123
    >>> model.foo = "456"  # OK; "456" can be parsed as int
    >>> model.foo
    456
    >>> model.foo = None  # OK
    >>> model.foo is None
    True
    >>> validate(model)  # OK
    >>> del model.foo
    >>> model.foo
    Unset
    >>> validate(model)  # OK

Using ``modelity.typing.StrictOptional[T]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Allowed values:

* objects of type ``T``
* objects of type ``U`` that can be parsed as ``T``
* :obj:`modelity.unset.Unset`

Use cases:

* for declaring fields that must either be set to ``T`` or not set at all

Example:

.. testcode::

    from modelity.api import (
        Model, StrictOptional, model_postvalidator, validate, is_unset,
        UserError
    )

    class Response(Model):
        """Strict optional example model.

        This shows the practical use case; response object can either have
        result or error, never both. A separate user-defined hook is used for
        cross-field checks.
        """
        result: StrictOptional[dict]
        error: StrictOptional[str]

        @model_postvalidator()
        def _either_result_or_error(self):
            if not is_unset(self.result) and not is_unset(self.error):
                raise UserError("cannot pass both result and error in the response")

.. doctest::

    >>> model = Response()
    >>> validate(model)  # OK
    >>> model.result = {"value": 123}  # OK
    >>> model.error = None # FAIL; StrictOptional[T] forbids None
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Response':
      error:
        This field does not allow None; expected: Union[str, UnsetType] [code=modelity.NONE_NOT_ALLOWED, value_type=NoneType, expected_type=Union[str, UnsetType]]
    >>> model.error  # still unset
    Unset
    >>> model.error = "an error"  # OK; field was set...
    >>> validate(model)  # FAIL: ...but cross field checks will now fail
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Response':
      (empty):
        cannot pass both result and error in the response [code=modelity.USER_ERROR]
    >>> del model.error
    >>> validate(model)  # OK; now only `result` is present

Default values
^^^^^^^^^^^^^^

Using direct assignment
~~~~~~~~~~~~~~~~~~~~~~~

The most basic way of declaring default values for a model field is to declare
that field and assign it to a value that will become its default value:

.. testcode::

    from modelity.api import Model

    class DefaultExample(Model):
        foo: int = 123

.. doctest::

    >>> model = DefaultExample()  # OK; using 123 as default value for `foo`
    >>> model
    DefaultExample(foo=123)
    >>> another_model = DefaultExample(foo=456)  # OK; using 456 value for `foo`
    >>> another_model
    DefaultExample(foo=456)

Default values are no different than any other input values, so given the
example below if ``"789"`` is used as a default then it will be parsed into
integer number during model construction:

.. testcode::

    from modelity.api import Model

    class DefaultExample(Model):
        foo: int = "789"

.. doctest::

    >>> model = DefaultExample()
    >>> model
    DefaultExample(foo=789)

And if invalid value will be used as a default then creating model without args
will fail:

.. testcode::

    from modelity.api import Model

    class InvalidDefaultExample(Model):
        foo: int = "not an integer"

.. doctest::

    >>> model = InvalidDefaultExample()
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'InvalidDefaultExample':
      foo:
        Not a valid int value [code=modelity.PARSE_ERROR, value_type=str, expected_type=int]

.. important::

    Default values are currently not evaluated when declaring models, so pay
    attention to default values and their types when declaring those to avoid
    unexpected errors like the one above.

Mutable default values
~~~~~~~~~~~~~~~~~~~~~~

In Modelity you can safely use mutable values as field's defaults, as those are
deep copied when model is created. For example, you can set empty list as
default value for list field:

.. testcode::

    from modelity.api import Model

    class MutableExample(Model):
        foo: list[int] = []

And now, you don't have to initialize ``foo`` with empty list when constructing
models:

.. doctest::

    >>> model = MutableExample()
    >>> model.foo
    []
    >>> model.foo.append(123)  # Here we append first element
    >>> model.foo
    [123]

And the original default value is still an empty list:

.. doctest::

    >>> MutableExample.__model_fields__['foo'].field_info.default  # This is how field metadata can be accessed (there is a dedicated section on this topic)
    []

Using ``field_info`` helper
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Same functionality can be achieved when :func:`modelity.base.field_info` helper
is used in place of direct default value assignment. In fact, Modelity
automatically converts fixed default values to :class:`modelity.base.FieldInfo`
objects unless one is set explicitly using said function. Here's an example:

.. testcode::

    from modelity.api import Model, field_info

    class DefaultExample(Model):
        foo: int = field_info(default=123)  # same as `foo: int = 123`

Such solution gives you the possibility of adding more metadata to field than
just a default value. There will be more on this in the upcoming chapter.

Computed default values
~~~~~~~~~~~~~~~~~~~~~~~

Modelity also supports declaring default values by assigning factory function
instead of fixed static default. To do this you will also need
:func:`modelity.base.field_info` helper like in previous section. This is very
useful to get e.g. the current date and time when the model is created:

.. testcode::
    :hide:

    import datetime

    def utcnow():
        return datetime.datetime(2026, 1, 1, 10, 10)

.. testcode::

    import datetime

    from modelity.api import Model, field_info

    class Order(Model):
        items: list[str] = []
        created: datetime.datetime = field_info(default_factory=utcnow)  # `utcnow` is a no-argument function returning datetime

Now when the model is created, ``created`` field will be set to current date
and time in UTC:

.. doctest::

    >>> model = Order()
    >>> model
    Order(items=[], created=datetime.datetime(2026, 1, 1, 10, 10))

Attaching metadata to fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity supports attaching metadata to fields using
:func:`modelity.base.field_info` helper. It was already presented earlier and
used to declare default values, but let's now show some more examples. Consider
this one:

.. testcode::

    from modelity.api import Model, field_info

    class OrderItem(Model):
        name: str = field_info(title="Item name", examples=["apple", "banana", "orange"])
        quantity: int = field_info(title="Number of items")
        price: float = field_info(title="The price of a single unit")

These metadata does not take place in model processing, but can be used as a
source of additional data for external tools, like documentation generators. To
access these metadata, you have to use
:attr:`modelity.base.ModelMeta.__model_fields__` property:

.. doctest::

    >>> list(OrderItem.__model_fields__)  # list of field names
    ['name', 'quantity', 'price']
    >>> name = OrderItem.__model_fields__["name"]  # get `name` field
    >>> name.field_info.title
    'Item name'
    >>> name.field_info.examples
    ['apple', 'banana', 'orange']

Please proceed to :func:`modelity.base.field_info` for more information.

Using ``typing.Annotated`` and field-level constraints
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity comes with :mod:`modelity.constraints` module containing field-level
constraints that can be attached to fields using :obj:`typing.Annotated` type
modifier. Such declared fields are automatically verified when field is set, or
when model is validated. The latter is crucial for fields with mutable
containers, where modifying container's content may invalidate the constraint.

Here's an example:

.. testcode::

    from typing import Annotated

    from modelity.api import Model, MinLen, Gt, Ge

    class OrderItem(Model):
        name: Annotated[str, MinLen(1)]  # empty string is not allowed
        quantity: Annotated[int, Gt(0)]  # greater than, i.e. > 0
        price: Annotated[float, Ge(0)]  # greater than or equal to, i.e. >= 0

    class Order(Model):
        items: Annotated[list[OrderItem], MinLen(1)]  # at least one order

Now let's create first buggy **OrderItem** and see what's happening:

.. doctest::

    >>> buggy = OrderItem(name="", quantity=-1, price=-1.5)
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 3 parsing errors for type 'OrderItem':
      name:
        Expected length >= 1 [code=modelity.INVALID_LENGTH, value_type=str, min_length=1]
      price:
        Value must be >= 0 [code=modelity.OUT_OF_RANGE, value_type=float, min_inclusive=0]
      quantity:
        Value must be > 0 [code=modelity.OUT_OF_RANGE, value_type=int, min_exclusive=0]

As you can see, the constraints are failing, as we've intentionally set
incorrect values for fields. Let's now create a valid model and try to set one
of its field to an invalid value:

.. doctest::

    >>> apple = OrderItem(name="apple", quantity=1, price=1.5)  # OK
    >>> apple.name = ""  # FAIL; empty string is not allowed
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'OrderItem':
      name:
        Expected length >= 1 [code=modelity.INVALID_LENGTH, value_type=str, min_length=1]

The constraints are automatically checked when fields are modified and
:exc:`modelity.exc.ParsingError` reported then gives an instant feedback.
However, if mutable field is modified (not overwritten) then the constrains
will not be re-evaluated:

.. doctest::

    >>> order = Order(items=[apple])  # OK; initialized with one element
    >>> len(order.items)
    1
    >>> order.items.clear()  # Remove all items from the list; NO ERROR!
    >>> len(order.items)
    0

Why there is no error despite the fact that now the minimum length constraint
is broken? Well, the field itself WAS NOT changed (it still points to the same
list object) therefore constraint check was not triggered. But the model is in
fact invalid now -- we can check that using :func:`modelity.helpers.validate`
helper function:

.. doctest::

    >>> from modelity.helpers import validate
    >>> validate(order)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Order':
      items:
        Expected length >= 1 [code=modelity.INVALID_LENGTH, min_length=1]

Validating model re-evaluates field-level constraints and that makes the thing
working as a whole even for mutable fields. This is one of the reasons why
Modelity have separated data processing into two distinct stages.

Using inheritance
^^^^^^^^^^^^^^^^^

In Modelity models are created by inheriting from :class:`modelity.base.Model`
base class. But every single created model class can be a base class itself and
this can be used to create bases with common fields and/or user-defined hooks.
Consider following example:

.. testcode::

    from modelity.api import Model, field_postprocessor

    class Base(Model):
        id: int

        @field_postprocessor()
        def _strip_string_values(cls, value):
            if isinstance(value, str):
                return value.strip()
            return value

    class Author(Base):
        first_name: str
        last_name: str

    class Book(Base):
        title: str
        author: Author

The example above introduced a :func:`modelity.hooks.field_postprocessor` hook
that runs when field is set and after successful type parsing. Since it was
declared without arguments, the hook will be called for every field and if
value is a string it will be stripped.

.. note::

    Check :ref:`guide_hooks` for more information about user-defined hooks.

Since the hook was declared in base class, both **Author** and **Book** models
are now automatically using it, as well as the ``id`` field that was also
inherited:

.. doctest::

    >>> author = Author(id=1, first_name=" John", last_name="Doe ")  # Leading and trailing spaces will be stripped
    >>> book = Book(id=2, author=author, title=" Good Old Book ")  # same here
    >>> author
    Author(id=1, first_name='John', last_name='Doe')
    >>> book.title
    'Good Old Book'

Having hooks that are performing common cleanup operations on data in one place
is a recommended practice according to DRY principle and using inheritance to
achieve that is one option.

Using mixins
^^^^^^^^^^^^

A more elastic way of reusing common functionality is to use **mixins** instead
or in addition to base classes. Mixins will let you wrap hooks in reusable and
named classes that can later be injected to models without breaking or
rebuilding entire inheritance tree. And, it is also quite easy to add more
mixins if needed.

.. important::

    Only hooks can currently be provided via mixins; fields must still rely on
    inheritance mechanism.

Let's rewrite previous example and now let's extract string stripping hook to a
separate **SupportsStripping** mixin:

.. testcode::

    from modelity.api import Model, field_postprocessor

    class Base(Model):  # This is our base model
        id: int

    class SupportsStripping:  # This is our mixin with string stripping hook

        @field_postprocessor()
        def _strip_string_values(cls, value):
            if isinstance(value, str):
                return value.strip()
            return value

    class Author(Base, SupportsStripping):  # Use mixin
        first_name: str
        last_name: str

    class Book(Base, SupportsStripping):  # Same here
        title: str
        author: Author

And now, the models behave exactly the same as previously, but are now sharing
string striping hook via mixin:

.. doctest::

    >>> author = Author(id=1, first_name=" John", last_name="Doe ")  # Leading and trailing spaces will be stripped
    >>> book = Book(id=2, author=author, title=" Good Old Book ")  # same here
    >>> author
    Author(id=1, first_name='John', last_name='Doe')
    >>> book.title
    'Good Old Book'

Working with model objects
--------------------------

Constructing model objects
^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's consider following model declaration:

.. testcode::

    from modelity.api import Model

    class OrderItem(Model):
        name: str  # required
        quantity: int = 1  # required, but with default value
        price: float  # required

To create instance of such model you have to pass field names and corresponding
values as arguments for a built-in keyword-only constructor:

.. doctest::

    >>> apples = OrderItem(name="apple", price=1.5)  # sets 'name' and 'apple', 'quantity' uses default value
    >>> apples
    OrderItem(name='apple', quantity=1, price=1.5)
    >>> oranges = OrderItem(name="orange", quantity=2, price=2.5)  # override default set for 'quantity'
    >>> oranges
    OrderItem(name='orange', quantity=2, price=2.5)

If you forget about required fields, Modelity will inform you with following
error:

.. doctest::

    >>> empty = OrderItem()  # 'name' and 'price' must be set
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 2 parsing errors for type 'OrderItem':
      name:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]
      price:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]

Customizing model construction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Overloading ``__init__`` method is **strongly discouraged** in Modelity as it
may break the interface that is expected by Modelity internals. However, if you
really need to do so, here's a safe boilerplate example:

.. testcode::

    from modelity.api import Model

    class OrderItem(Model):
        name: str
        quantity: int
        price: float

        def __init__(self, **kwargs):  # IMPORTANT!
            if "quantity" not in kwargs:  # before "real" init
                kwargs["quantity"] = 1
            super().__init__(**kwargs)  # IMPORTANT!
            if self.price < 0:  # after "real" init
                self.price = 0

In general, the rule of thumb is to keep it keyword-only and to **always** call
base class constructor. Now let's check how this works:

.. doctest::

    >>> bananas = OrderItem(name="banana", price=-2.0)
    >>> bananas
    OrderItem(name='banana', quantity=1, price=0.0)

A much better and **recommended** solution is to create per-model factory
method that has its own, user-defined interface and is not part of Modelity
internals. For example, you may want to create models using positional
arguments. Here's an example of such factory method:

.. testcode::

    from modelity.api import Model

    class OrderItem(Model):
        name: str
        quantity: int
        price: float

        @classmethod
        def create(cls, name: str, price: float, quantity: int=1) -> "OrderItem":
            return cls(name=name, quantity=quantity, price=price)

Besides allowing to pass arguments in either keyword or positional way the
custom method can also reorder arguments and set some defaults. Underneath the
method is still calling built-in constructor. Here's how this can be used:

.. doctest::

    >>> onions = OrderItem.create("onion", 0.75, quantity=3)
    >>> onions
    OrderItem(name='onion', quantity=3, price=0.75)

Unset fields
^^^^^^^^^^^^

Modelity handles unset fields using special :obj:`modelity.unset.Unset`
sentinel, which is a singleton instance of :class:`modelity.unset.UnsetType`
class. This special value is used by Modelity to explicitly represent fields
that were not set in the constructor or fields that were removed from the model
after it was created.

All non-required and unsettable fields are **implicitly** unset if no other
default value was given:

.. testcode::

    from modelity.api import Model, StrictOptional

    class Example(Model):
        foo: StrictOptional[int]
        bar: StrictOptional[str]

.. doctest::

    >>> model = Example()  # No argument given
    >>> model.foo
    Unset
    >>> model.foo
    Unset

However, it is usually better to **explicitly** set those fields to ``Unset``,
as it plays better with code linters and type checking tools (i.e. no warnings
about missing required params):

.. testcode::

    from modelity.api import Model, StrictOptional, Unset

    class Example(Model):
        foo: StrictOptional[int] = Unset  # Same behavior as before, but explicit
        bar: StrictOptional[str] = Unset

Modelity provides a :func:`modelity.unset.is_unset` helper that can be used to
check if the field is set or not. It is recommended to use this helper instead
of manually checking ``if model.field is not Unset`` as it performs **type
narrowing**, so LSPs will automatically know the remaining types:

.. doctest::

    >>> from modelity.api import is_unset
    >>> model = Example()
    >>> is_unset(model.foo)
    True
    >>> model.foo = 123
    >>> is_unset(model.foo)  # not unset; the LSP will know that `foo` is an integer
    False

Inspecting models using ``repr`` function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All models provide default implementation of :meth:`object.__repr__` magic
method that will print text representation of the model. The representation
includes model class name and its field names with current values. For example:

.. testcode::

    from modelity.api import Model, Unset, LooseOptional

    class Dummy(Model):
        foo: int
        bar: Optional[str] = None
        baz: LooseOptional[float] = Unset

.. doctest::

    >>> repr(Dummy(foo=123))
    'Dummy(foo=123, bar=None, baz=Unset)'
    >>> repr(Dummy(foo=123, baz=3.14))
    'Dummy(foo=123, bar=None, baz=3.14)'

Comparing two model instances
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity provides built-in implementation of the :meth:`object.__eq__` method
for checking if two Python objects are equal. Two model objects, ``a`` and
``b``, are equal if and only if all of these statements are true:

* both objects are instances of **same** model type,
* both objects have exactly same fields set,
* all fields that are set are equal.

Some examples:

.. testcode::

    from modelity.api import Model, LooseOptional

    class Foo(Model):
        spam: LooseOptional[int]

    class Bar(Model):
        spam: LooseOptional[int]

.. doctest::

    >>> Foo() == Foo()
    True
    >>> Foo(spam=123) == Foo(spam=123)
    True
    >>> Foo() == Bar()  # Two different types
    False
    >>> Foo(spam=123) == Foo()  # Different amount of fields set
    False
    >>> Foo(spam=123) == Foo(spam=456)  # Different field values
    False

Checking if field is set
^^^^^^^^^^^^^^^^^^^^^^^^

To check if a field is set, ``in`` operator can be used:

.. testcode::

    from modelity.api import Model

    class Dummy(Model):
        a: LooseOptional[int]
        b: LooseOptional[int]

.. doctest::

    >>> foo = Dummy()
    >>> "a" in foo
    False
    >>> foo.a = 123
    >>> "a" in foo
    True
    >>> foo.a = None  # IMPORTANT: None is a first class value!
    >>> "a" in foo
    True
    >>> del foo.a
    >>> "a" in foo
    False

.. important::

    In Modelity, unset fields are all fields that are set to
    :obj:`modelity.unset.Unset` object, so assigning a field with ``Unset``
    manually is basically equivalent of using ``del`` operator:

    .. doctest::

        >>> from modelity.unset import Unset
        >>> bar = Dummy(a=123)
        >>> "a" in bar
        True
        >>> bar.a = Unset
        >>> "a" in bar
        False

Iteration over set fields only
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity supplies models with :meth:`object.__iter__` method implementation
that iterates through the model, in field-defined order, and yields names of
fields that are currently set:

.. testcode::

    from modelity.api import Model, LooseOptional

    class IterExample(Model):
        a: int
        b: int
        c: LooseOptional[int]
        d: LooseOptional[int]

.. doctest::

    >>> one = IterExample(a=1, b=2)
    >>> list(one)
    ['a', 'b']
    >>> two = IterExample(a=1, b=2, c=3)
    >>> list(two)
    ['a', 'b', 'c']

As a bonus, there also is a helper :func:`modelity.helpers.has_fields_set` that
can be used to check if any of model fields is set:

.. doctest::

    >>> from modelity.api import has_fields_set
    >>> has_fields_set(one)
    True
    >>> has_fields_set(two)
    True
    >>> one.a = one.b = Unset  # NOTE: Presence of required fields is double-checked during later validation
    >>> has_fields_set(one)
    False

Setting and getting attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since models in Modelity are **mutable** by design, assigning value to a field
of an existing model object invokes exactly the same value parsing logic as
when model constructor is used. Here are some examples:

.. testcode::

    from modelity.api import Model, LooseOptional

    class SetGetDelExample(Model):
        foo: LooseOptional[int]

.. doctest::

    >>> model = SetGetDelExample()  # OK; no required fields
    >>> model.foo  # getting attribute; it is Unset now
    Unset
    >>> model.foo = 123  # setting attribute; parsing logic is executed
    >>> model.foo
    123
    >>> model.foo = "spam"  # FAIL; neither int, nor it can be parsed as int
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'SetGetDelExample':
      foo:
        Not a valid int value [code=modelity.PARSE_ERROR, value_type=str, expected_type=int]
    >>> model.foo  # old value remains
    123

Deleting attributes
^^^^^^^^^^^^^^^^^^^

Attributes can be deleted from model object, but this is just a syntactic sugar
over assignment of an attribute with :obj:`modelity.unset.Unset` value. Any
model field can be deleted from the model after successful construction. This
is safe for as long as the model is later (re-)validated with
:func:`modelity.helpers.validate` function. For example:

.. testcode::

    from modelity.api import Model, validate

    class Dummy(Model):
        foo: int

.. doctest::

    >>> dummy = Dummy(foo=123)
    >>> dummy.foo
    123
    >>> del dummy.foo
    >>> dummy.foo
    Unset
    >>> validate(dummy)  # FAIL; we've just deleted required field
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Dummy':
      foo:
        This field is required [code=modelity.REQUIRED_MISSING]
    >>> dummy.foo = 456
    >>> dummy.foo
    456
    >>> validate(dummy)  # OK

Applying visitors to models
^^^^^^^^^^^^^^^^^^^^^^^^^^^

One of Modelity design decisions was to use **visitor pattern** to separate
model structure from algorithms operating on that structure.

Modelity provides few built-in visitor implementations (for validation and
serialization) available in :mod:`modelity.visitors` module, an ABC
:class:`modelity.base.ModelVisitor` for creating custom ones from a scratch,
and a :meth:`modelity.base.Model.accept` method for applying visitors on
models.

There is also a :mod:`modelity.helpers` module containing helpers for hiding
boilerplate code (e.g. :func:`modelity.helpers.dump` for serialization or
:func:`modelity.helpers.validate` for validation) but you still can instantiate
and run visitors manually whenever needed.

Here's a simple example:

.. testcode::

    from modelity.api import Model, Loc

    class OrderItem(Model):
        name: str
        quantity: int
        price: float

    class Order(Model):
        id: int
        items: list[OrderItem]

Now let's create some order object:

.. doctest::

    >>> apple = OrderItem(name="apple", quantity=1, price=2.5)
    >>> banana = OrderItem(name="banana", quantity=2, price=1.5)
    >>> orange = OrderItem(name="orange", quantity=4, price=0.75)
    >>> order = Order(id=1, items=[apple, banana, orange])

And finally, let's dump it to dict using :class:`modelity.visitors.DumpVisitor`
visitor:

.. doctest::

    >>> from modelity.api import DumpVisitor
    >>> out = {}
    >>> visitor = DumpVisitor(out)
    >>> order.accept(visitor, Loc())
    >>> out
    {'id': 1, 'items': [{'name': 'apple', 'quantity': 1, 'price': 2.5}, {'name': 'banana', 'quantity': 2, 'price': 1.5}, {'name': 'orange', 'quantity': 4, 'price': 0.75}]}

Data processing pipeline
------------------------

Input data parsing
^^^^^^^^^^^^^^^^^^

Data parsing happens when a new model instance is created, when fields in
existing models are modified, or when mutable containers are modified. This
stage is executed on a field-level basis and its role is to ensure that data
stored in the model respects model field types, or to **reject** the input data
completely if it does not.

Failed parsing is signalled with :exc:`modelity.exc.ParsingError` exception
that is raised with all parsing errors collected for all fields.

Preprocessing chain
~~~~~~~~~~~~~~~~~~~

Preprocessing is an optional first step of data parsing that happens for an
individual fields if those have user-defined **preprocessors** assigned via
dedicated :func:`modelity.hooks.field_preprocessor` decorator. This decorator
can be declared for all fields, or for a given subset of fields depending on
whether or not and which field names are given during declaration.

Preprocessors can report errors either by raising
:exc:`modelity.exc.UserError`, or by manually creating
:class:`modelity.error.Error` object and adding it to the ``errors`` list (see
hook :func:`modelity.hooks.field_preprocessor` for more details on this). If
any of preprocessors report one or more errors, the parsing as a whole will
fail.

Preprocessors are used to clean up and normalize the data before it is passed
further to the type parsing step. The very common use case is to restrict input
data just to a subset of input types (i.e. only JSON-compatible ones) or to
perform actions like string stripping to remove whitespace characters.

The data flow for preprocessing chain looks as follows::

    (raw input) ->
    [1st preprocessor -> [2nd preprocessor -> ... -> N-th preprocessor ->]]
    (preprocessed output)

Here's an example:

.. testcode::

    from modelity.exc import UserError
    from modelity.base import Model
    from modelity.hooks import field_preprocessor

    class JsonRestrictingModel(Model):
        """Base class for models allowing only JSON-compatible input values."""

        @field_preprocessor()  # Will run for all fields
        def _restrict_input(cls, value):
            if value is not None and not isinstance(value, (int, float, str, bool, list, dict)):
                raise UserError("non JSON-compatible value")  # Will terminate parsing
            return value

    class OrderItem(JsonRestrictingModel):
        name: str
        quantity: int
        price: float

        @field_preprocessor("name", "quantity", "price")  # Fields for which the hook will run
        def _strip_strings(cls, value):
            if isinstance(value, str):
                return value.strip()  # call strip() only if input value is a string
            return value

.. doctest::

    >>> apples = OrderItem(name=" apple ", quantity=" 2 ", price=" 3.25 ")  # This would fail without '_strip_strings' preprocessor
    >>> apples
    OrderItem(name='apple', quantity=2, price=3.25)
    >>> apples.name = object()
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'OrderItem':
      name:
        non JSON-compatible value [code=modelity.USER_ERROR, value_type=object]

Type parsing
~~~~~~~~~~~~

Type parsing runs in a field-level scope, individually for each field, on the
preprocessed data delivered by the last preprocessor set for a field being
currently parsed, or for raw input data if no preprocessors were found.

Parsing step runs the core logic of Modelity built-in parsing system and
ensures that all fields of a model have the right value (i.e. instance of type
set for that field), or otherwise tries to parse input as the type field
expects. Finally, if input value is neither instance of the right type, nor it
can be parsed as one, parsing step fails and :class:`modelity.error.Error` is
reported with precise cause and :exc:`modelity.exc.ParsingError` is raised.

The data flow for type parsing looks as follows::

    (preprocessed output) -> type parser -> (parsed output)

Although we've already seen that in action, let's have some more examples as a
recap:

.. testcode::

    from modelity.base import Model

    class OrderItem(Model):
        name: str
        quantity: int
        price: float

    class Order(Model):
        items: list[OrderItem]

Now, let's take a look at the following example:

.. doctest::

    >>> apples = OrderItem(name="apple", quantity=3, price=1.5)  # The right types
    >>> apples
    OrderItem(name='apple', quantity=3, price=1.5)
    >>> oranges = OrderItem(name="orange", quantity="3", price="1.5")  # Not the right types, but successfully parsed
    >>> oranges
    OrderItem(name='orange', quantity=3, price=1.5)
    >>> incorrect = OrderItem(name="incorrect", quantity="three", price="one and the half")  # FAIL: Cannot parse
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 2 parsing errors for type 'OrderItem':
      price:
        Not a valid float value [code=modelity.PARSE_ERROR, value_type=str, expected_type=float]
      quantity:
        Not a valid int value [code=modelity.PARSE_ERROR, value_type=str, expected_type=int]

First object, ``apples``, was created using the exact value types model
expects. Second object, ``oranges``, was also created successfully, but
original input given as string was parsed to the right type. Third example,
``incorrect``, has failed as Modelity could not parse given strings as integer
and float numbers.

Same logic happens when existing models are modified:

.. doctest::

    >>> apples.quantity = "4"  # OK; this can be parsed
    >>> apples.quantity
    4
    >>> oranges.price = 1  # OK; int can be parsed as float
    >>> oranges.price
    1.0
    >>> oranges.quantity = "four"  # FAIL; cannot parse `four` as int
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'OrderItem':
      quantity:
        Not a valid int value [code=modelity.PARSE_ERROR, value_type=str, expected_type=int]
    >>> oranges.quantity  # The old value remains intact
    3

Now let's take a look at few more examples showing how parsing of the container
types work. Parsing containers involves both parsing container itself, and each
individual item:

* OK; all elements already have the right type

    .. doctest::

        >>> first = Order(items=[apples, oranges])
        >>> first.items[0] is apples
        True
        >>> first.items[1] is oranges
        True

* OK; :class:`dict` can be parsed as **OrderItem** if all required fields are
  present and all fields have the right values:

    .. doctest::

        >>> second = Order(items=[{"name": "strawberry", "quantity": "7", "price": "3.5"}])
        >>> second.items[0]
        OrderItem(name='strawberry', quantity=7, price=3.5)

* FAIL; cannot parse :class:`int` value as a :class:`list` container

    .. doctest::

        >>> fail1 = Order(items=123)
        Traceback (most recent call last):
          ...
        modelity.exc.ParsingError: Found 1 parsing error for type 'Order':
          items:
            Not a valid value; expected: list[OrderItem] [code=modelity.INVALID_TYPE, value_type=int, expected_types=[list[OrderItem]], allowed_types=[Sequence], forbidden_types=[str, bytes]]

* FAIL; cannot parse :class:`int` as **OrderItem**

    >>> fail2 = Order(items=[apples, oranges, 123])  # FAIL; cannot parse 123 as OrderItem
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Order':
      items.2:
        Not a valid value; expected: OrderItem [code=modelity.INVALID_TYPE, value_type=int, expected_types=[OrderItem], allowed_types=[Mapping]]

* FAIL; empty dict does not contain all fields required by **OrderItem** model:

    >>> fail3 = Order(items=[apples, oranges, {}])  # FAIL; the dict does not have all required fields set
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 3 parsing errors for type 'Order':
      items.2.name:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]
      items.2.price:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]
      items.2.quantity:
        This field is required [code=modelity.REQUIRED_MISSING, value_type=UnsetType]

Postprocessing chain
~~~~~~~~~~~~~~~~~~~~

Postprocessing is an optional last step of data parsing that happens for an
individual fields if those have user-defined **postprocessors** assigned via
dedicated :func:`modelity.hooks.field_postprocessor` decorator. This decorator
can be declared for all fields, or for a given subset of fields depending on
whether or not and which field names are given during declaration.

Postprocessors can report errors either by raising
:exc:`modelity.exc.UserError`, or by manually creating
:class:`modelity.error.Error` object and adding it to the ``errors`` list (see
hook :func:`modelity.hooks.field_postprocessor` for more details on this). If
any of postprocessors report one or more errors, the parsing as a whole will
fail.

Postprocessors receive data from type parser and can assume that input value
for the first preprocessor already has the right type (there is no need to
check that). The role of postprocessors is to perform field-level validation,
data normalization that does not affect field's type, or both. The value
returned by the last postprocessor in the chain will be used as field's value.

The data flow for postprocessing chain looks as follows::

    (parsed output) ->
    [1st postprocessor -> [2nd postprocessor -> ... -> N-th postprocessor ->]]
    (field value)

.. important::

    There is no more type checking after preprocessing step, so preprocessors
    can potentially **alter** field type without being noticed. This is fine
    for as long as the new type is **compatible** with field's type (e.g. is a
    subclass), but **SHOULD BE** avoided for incompatible types as those will
    break the contract enforced by the model.

Here's a practical example of using postprocessing hook:

.. testcode::

    import math

    from modelity.base import Model
    from modelity.hooks import field_postprocessor

    class Vec2D(Model):
        """Model representing a 2-dimensional vector."""
        x: float
        y: float

        def length(self):
            """Compute vector's length."""
            return math.sqrt(self.x**2 + self.y**2)

        def normalized(self) -> "Vec2D":
            """Compute normalized version of this vector."""
            l = self.length()
            return Vec2D(x=self.x/l, y=self.y/l)

    class Object2D(Model):
        """Model representing 2-dimensional object."""
        pos: Vec2D
        dir: Vec2D
        speed: float

        @field_postprocessor("dir")  # Applied only to `dir` vector
        def _normalize_direction(cls, value: Vec2D):
            return value.normalized()  # `value` is guaranteed to be Vec2D

.. doctest::

    >>> p = Vec2D(x=1, y=3)  # position vector
    >>> d = Vec2D(x=5, y=5)  # direction vector
    >>> obj = Object2D(pos=p, dir=d, speed=0.75)  # here the postprocessor will be used on `d`
    >>> obj.pos is p  # This one was not modified by postprocessor
    True
    >>> obj.dir is not d  # This one was normalized by postprocessor
    True
    >>> obj.dir
    Vec2D(x=0.7071067811865475, y=0.7071067811865475)

.. _fixup_step:

Adding missing or derived data to models
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using ``after_field_set`` hook
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Modelity provides :func:`modelity.hooks.after_field_set` hook that can be used
to wrap a function to be executed when a field is set to a valid value. The
hook can be triggered by any model field (if declared without args) or with any
of the given fields (otherwise).

Here's an example:

.. testcode::

    import datetime

    from modelity.base import Model
    from modelity.loc import Loc
    from modelity.typing import Deferred
    from modelity.hooks import after_field_set

    class FileInfo(Model):
        path: str
        size: int
        created: datetime.datetime
        modified: Deferred[datetime.datetime]  # Make it deferred, so it will not be required during construction

        @after_field_set("path", "size", "created")
        def _reset_modified(self, loc: Loc, value: datetime.datetime):
            if loc[-1] == "created":
                self.modified = value  # Modified shouldn't precede `created`
            else:
                self.modified = datetime.datetime.now()  # Update modification time when `path` or `size` is changed

.. doctest::

    >>> foo = FileInfo(path="/foo.txt", size=1024, created=datetime.datetime.now())  # Will also set `modified`
    >>> foo.created == foo.modified
    True

And same will happen if ``created`` is later modified:

.. doctest::

    >>> foo.created = datetime.datetime(1999, 1, 1, 10, 10)
    >>> foo.modified
    datetime.datetime(1999, 1, 1, 10, 10)

And if parsing of ``created`` field fails, the hook will not be executed:

.. doctest::

    >>> foo.created = "invalid"
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'FileInfo':
      created:
        Not a valid datetime format; expected one of: YYYY-MM-DDThh:mm:ssZZZZ, YYYY-MM-DDThh:mm:ss.ffffffZZZZ, YYYY-MM-DDThh:mm:ss, YYYY-MM-DDThh:mm:ss.ffffff, YYYY-MM-DD hh:mm:ss ZZZZ, YYYY-MM-DD hh:mm:ss.ffffff ZZZZ, YYYY-MM-DD hh:mm:ss, YYYY-MM-DD hh:mm:ss.ffffff, YYYYMMDDThhmmssZZZZ, YYYYMMDDThhmmss.ffffffZZZZ, YYYYMMDDThhmmss, YYYYMMDDThhmmss.ffffff, YYYYMMDDhhmmssZZZZ, YYYYMMDDhhmmss.ffffffZZZZ, YYYYMMDDhhmmss, YYYYMMDDhhmmss.ffffff [code=modelity.INVALID_DATETIME_FORMAT, value_type=str, expected_formats=['YYYY-MM-DDThh:mm:ssZZZZ', 'YYYY-MM-DDThh:mm:ss.ffffffZZZZ', 'YYYY-MM-DDThh:mm:ss', 'YYYY-MM-DDThh:mm:ss.ffffff', 'YYYY-MM-DD hh:mm:ss ZZZZ', 'YYYY-MM-DD hh:mm:ss.ffffff ZZZZ', 'YYYY-MM-DD hh:mm:ss', 'YYYY-MM-DD hh:mm:ss.ffffff', 'YYYYMMDDThhmmssZZZZ', 'YYYYMMDDThhmmss.ffffffZZZZ', 'YYYYMMDDThhmmss', 'YYYYMMDDThhmmss.ffffff', 'YYYYMMDDhhmmssZZZZ', 'YYYYMMDDhhmmss.ffffffZZZZ', 'YYYYMMDDhhmmss', 'YYYYMMDDhhmmss.ffffff']]
    >>> foo.modified == foo.created
    True
    >>> foo.modified
    datetime.datetime(1999, 1, 1, 10, 10)

And also, when any of the fields is changed, model will automatically update
``modified`` time:

.. doctest::

    >>> foo.modified == foo.created
    True
    >>> foo.path = "/bar.txt"  # Will trigger the hook and update modification time
    >>> foo.modified == foo.created
    False

You can of course add some additional conditions, like setting the value only
if it is unset.

.. important::

    This hook must be properly configured to avoid recursion errors. In the
    example above, ``modified`` field was intentionally ignored as changing it
    would also cause the hook to fire, and that would cause ``modified`` to be
    altered... causing infinite recursion error.

Using ``model_fixup`` hook
~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`modelity.hooks.after_field_set` hook shown earlier will not be
called when modifying mutable fields in-place. To overcome this obstacle, a
dedicated :func:`modelity.hooks.model_fixup` hook is also provided. It operates
at the model level and can only be run if :func:`modelity.helpers.fixup` helper
is explicitly called on a model.

Here's an example:

.. testcode::

    from modelity.base import Model
    from modelity.hooks import model_fixup
    from modelity.helpers import fixup

    class OrderItem(Model):
        name: str
        quantity: int
        price: float

    class Order(Model):
        items: list[OrderItem] = []
        total: float = 0.0

        @model_fixup()
        def _adjust_total(self):
            self.total = sum(x.quantity * x.price for x in self.items)

.. doctest::

    >>> apples = OrderItem(name="apple", quantity=2, price=1.5)
    >>> oranges = OrderItem(name="orange", quantity=3, price=2.0)
    >>> order = Order()
    >>> order.total
    0.0
    >>> order.items.append(apples)
    >>> order.items.append(oranges)
    >>> order.total  # No change
    0.0
    >>> fixup(order)  # Here the `_adjust_total` will be called
    >>> order.total
    9.0

The mechanism of model fixing up is backed up with a dedicated visitor (see
:class:`modelity.visitors.FixupVisitor`) and that brings the possibility
of running all model fixup hooks for the entire model tree using just a single
call to :func:`modelity.helpers.fixup` function for the root model only. For
example, let's now create a collection of orders:

.. testcode::

    from modelity.base import Model

    class UserOrders(Model):
        login: str
        orders: list[Order] = []
        total: float = 0.0

        @model_fixup()
        def _adjust_user_total(self):
            self.total = sum(x.total for x in self.orders)

.. doctest::

    >>> apples = OrderItem(name="apple", quantity=2, price=1.5)
    >>> oranges = OrderItem(name="orange", quantity=3, price=2.0)
    >>> order = Order()
    >>> order.items.append(apples)
    >>> order.items.append(oranges)
    >>> user_orders = UserOrders(login="john.doe")
    >>> user_orders.orders.append(order)
    >>> fixup(user_orders)  # Will run both `_adjust_total` for Order model, and `_adjust_user_total` for UserOrders model
    >>> user_orders.total
    9.0

Validating models
^^^^^^^^^^^^^^^^^

Modelity does not validate models automatically, but instead lets you decide if
and when the models will be validated. Recommended way of validating models is
to use :func:`modelity.helpers.validate` helper. Alternatively, if you need more
fine-tuned customization, you can subclass
:class:`modelity.visitors.ValidationVisitor` built-in default validation visitor
(the one used by helper) or even to create your own validation visitor from
scratch (for advanced users).

Errors reported during validation step are all collected and raised as a single
:class:`modelity.exc.ValidationError` exception. This is different from
:class:`modelity.exc.ParsingError` used during parsing, so you can
differentiate errors raised at parsing step from the errors raised during
validation. This may be useful especially when loading complete models from
untrusted external data.

Unlike parsing step, where single error is causing instant full stop for a
processed field, all validators are always allowed to execute even if there
already are errors reported (with exception of
:func:`modelity.hooks.model_prevalidator` that can be used to skip remaining
validators for a model it was declared in).

.. note::

    Both exceptions inherit from same :class:`modelity.exc.ModelError`, so you
    can catch that if you don't care at what phase the exception was raised.

Built-in validation, like input data parsing, is divided into user-pluggable
steps that will be explained in details in the next sections.

.. important::

    Modelity assumes that validators have **no side effects**. In other words,
    validators **must not** modify model being validated in any way. Models are
    **read only** from the validators point of view. Any modifications must be
    done **before** validation either with manual field setting, or by using
    **fixup hooks** (see :ref:`fixup_step` for more details). The only dynamic
    data allowed to be modified (if really needed) is user-defined **context**
    object passed to validators. See :ref:`validate_with_context` for more
    details.

Model prevalidation chain
~~~~~~~~~~~~~~~~~~~~~~~~~

Model-level prevalidators can be declared using
:func:`modelity.hooks.model_prevalidator` hook. Model prevalidators are
executed before any other validators (even built-in ones like check of required
fields presence) and can be used to perform cross-field validation with
optional skipping of other validators (including built-in validators) for the
current model and all its nested models (if it has any). There can be multiple
model prevalidators defined and in such case all are executed in their
declaration order.

Here's a practical example of using model prevalidator to conditionally skip
validation of blog post if it is a draft:

.. testcode::

    from typing import Literal

    from modelity.api import Model, UserError, Deferred, model_prevalidator, validate

    class BlogPost(Model):
        title: Deferred[str]  # We will be filling these fields progressively
        content: Deferred[str]
        tags: list[str] = []
        status: Deferred[Literal["draft", "published"]] = "draft"  # By default it is a draft

        @model_prevalidator()
        def _check_draft_status(self, ctx):
            if self.status == "draft":
                # In draft mode, skip all other validations
                return True
            # Otherwise, proceed with normal validation
            return

.. doctest::

    >>> post = BlogPost(title="A story to tell")  # Just a title, no content yet
    >>> post.status
    'draft'
    >>> validate(post)  # OK; validation skipped, as `post` is a draft
    >>> post.status = "published"  # Let's now try to publish our post
    >>> validate(post)  # FAIL; content is still missing
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'BlogPost':
      content:
        This field is required [code=modelity.REQUIRED_MISSING]
    >>> post.content = "A long, long time ago..."
    >>> validate(post)  # OK

This example demonstrates how model prevalidator can be used to implement
conditional validation logic, such as allowing incomplete data in draft mode
while enforcing strict validation for published content.

Built-in validation
~~~~~~~~~~~~~~~~~~~

When model prevalidators are done, then built-in validation runs on a per-field
basis. Built-in validation ensures that all required fields are present (both
construction-time required, and validation-time required), prevents
non-unsettable fields (like :obj:`typing.Optional`) from being left unset, and
re-runs field-level constraints declared using :obj:`typing.Annotated` type
wrapper with constraints from :mod:`modelity.constraints` module.

Here's a brief example:

.. testcode::

    from typing import Annotated, Optional

    from modelity.api import Model, Deferred, MinLen, validate

    class DummyModel(Model):
        foo: int  # construction-time required
        bar: Deferred[int]  # validation-time required
        baz: Optional[str] = None  # equivalent of Union[str, None]; `Unset` is not a valid value
        spam: Annotated[list, MinLen(1)] = [1]  # can be modified after creation, so it must be re-checked

.. doctest::

    >>> model = DummyModel(foo=123)  # OK; all required fields set
    >>> model
    DummyModel(foo=123, bar=Unset, baz=None, spam=[1])
    >>> validate(model)  # FAIL; deferred field `bar` is missing
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'DummyModel':
      bar:
        This field is required [code=modelity.REQUIRED_MISSING]
    >>> model.bar = 456
    >>> validate(model)  # OK
    >>> del model.baz  # make `baz` Unset
    >>> validate(model)  # FAIL; `baz` cannot be unset
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'DummyModel':
      baz:
        This field does not allow Unset; expected: Union[str, NoneType] [code=modelity.UNSET_NOT_ALLOWED, expected_type=Union[str, NoneType]]
    >>> model.baz = "baz"  # Set a value to `baz` field
    >>> validate(model)  # OK
    >>> model.spam.clear()  # Clear mutable field
    >>> model.spam
    []
    >>> validate(model)  # FAIL; MinLen(1) constraint failed
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'DummyModel':
      spam:
        Expected length >= 1 [code=modelity.INVALID_LENGTH, min_length=1]

Field validation chain
~~~~~~~~~~~~~~~~~~~~~~

Field-level validation chain can be configured for each field individually and
is executed **only** if the field **has value set**. To declare field-level
validator, you have to use :func:`modelity.hooks.field_validator` hook. Field
validators are best way to implement cross-field validation logic, where
validated field depends on one or more other fields. For example:

.. testcode::

    from modelity.api import Model, field_validator

    class RegistrationForm(Model):
        username: str
        password: str
        repeated_password: str

        @field_validator("repeated_password")
        def _check_if_same_as_password(self, value):
            if value != self.password:
                raise UserError("passwords do not match")

.. doctest::

    >>> from modelity.api import validate
    >>> form = RegistrationForm(username="john.doe", password="p@ssw0rd", repeated_password="passw0rd")
    >>> validate(form)  # FAIL; passwords don't match
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'RegistrationForm':
      repeated_password:
        passwords do not match [code=modelity.USER_ERROR]
    >>> form.repeated_password = "p@ssw0rd"
    >>> validate(form)  # OK

Location-based validation chain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Location-based validation kind of extends field-level validation explained in
previous section. It allows to validate based on location patterns, not just
field names. Thanks to this you can declare validator that belongs to the model
while reaching into nested structures. To declare location-based validation,
:func:`modelity.hooks.location_validator` hook must be used.

Location validators use period-separated paths relative to the model where
validator was declared. Each path element can either be a field name, a key in
a mapping, and index in sequence, or one of the following wildcards:

* ``*`` to match any number of path segments,
* ``?`` to match exactly one location segment.

For example:

.. testcode::

    from modelity.api import Model, UserError, location_validator

    class Address(Model):
        street: str
        city: str
        zip_code: str

    class Person(Model):
        name: str
        home_address: Address
        work_address: Address

        @location_validator("?.zip_code")
        def _validate_zip_code(self, value):
            if not value.isdigit() or len(value) != 5:
                raise UserError("invalid zip code")

.. doctest::

    >>> from modelity.api import validate
    >>> person = Person(
    ...     name="John",
    ...     home_address={"street": "123 Main St", "city": "Anytown", "zip_code": "12345"},
    ...     work_address={"street": "456 Office Rd", "city": "Anytown", "zip_code": "abcde"}
    ... )
    >>> validate(person)  # FAIL; invalid zip code in work_address
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Person':
      work_address.zip_code:
        invalid zip code [code=modelity.USER_ERROR]
    >>> person.work_address.zip_code = "67890"
    >>> validate(person)  # OK

.. important::

    Location validators are evaluated at runtime, so the cost of using those
    may be higher than other validators. It is usually better to use other
    validators (f.e. :func:`modelity.hooks.field_validator`) if same results
    can be achieved.

Model postvalidation chain
~~~~~~~~~~~~~~~~~~~~~~~~~~

Model-wide postvalidation is the final step of validation for a given model
instance. To declare postvalidator for a given model,
:func:`modelity.hooks.model_postvalidator` hook must be used. It is recommended
to use postvalidators as a default choice to attach model-wide validation to
models, unless you need validation skipping functionality.

Here's an example:

.. testcode::

    from modelity.api import Model, UserError, model_postvalidator

    class Person(Model):
        name: str
        age: int

        @model_postvalidator()
        def validate_age(self):
            if self.age < 0:
                raise UserError("Age cannot be negative")

.. doctest::

    >>> from modelity.api import validate
    >>> person = Person(name="John", age=-5)
    >>> validate(person)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Person':
      (empty):
        Age cannot be negative [code=modelity.USER_ERROR]
    >>> person.age = 30
    >>> validate(person)  # OK

Advanced validation
-------------------

.. _validate_with_context:

Validating with user-defined context
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity allows you to pass context object of your choice to validation chain
and access it from inside your validators. Thanks to this it is possible to
choose different validation strategies depending on the use case. For example,
you can use this feature to completely disable validation for models fetched
from a trusted source.

Since you need to call :func:`modelity.helpers.validate` at some point from
your application's code, you are also capable of passing your own context
object via ``ctx`` argument and access it from validators using the same
argument name. For Modelity, the context is completely transparent and it is
simply passed to all validators "as is" without any modifications.

For example:

.. testcode::

    from typing import Optional

    from modelity.api import Model, model_prevalidator, field_validator, UserError

    class User(Model):
        name: str

        @model_prevalidator()
        def _prevalidate(self, ctx: Optional[dict]):
            if ctx and ctx.get('trusted_source'):
                return True  # Skip other validators for this model if this is a trusted source

        @field_validator("name")
        def _validate_name(self, value):
            if len(value) < 3:
                raise UserError("Name must be at least 3 characters")

.. doctest::

    >>> from modelity.api import validate
    >>> user = User(name="Jo")
    >>> validate(user)  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: ...
    >>> user = User(name="Jo")
    >>> validate(user, ctx={'trusted_source': True})
    >>> user.name
    'Jo'

You can also create a mixin or a base class for an easier reuse of such
mechanism for any model:

.. testcode::

    from typing import Optional

    from modelity.api import Model, model_prevalidator, field_validator, UserError

    class TrustedSkips:  # Mixin declaration

        @model_prevalidator()
        def _prevalidate(self, ctx: Optional[dict]):
            if ctx and ctx.get('trusted_source'):
                return True  # Skip other validators for this model if this is a trusted source

    class User(Model, TrustedSkips):  # Mixin use
        name: str

        @field_validator("name")
        def _validate_name(self, value):
            if len(value) < 3:
                raise UserError("Name must be at least 3 characters")

.. doctest::

    >>> from modelity.api import validate
    >>> user = User(name="")
    >>> validate(user)  # FAIL; validation runs normally
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'User':
      name:
        Name must be at least 3 characters [code=modelity.USER_ERROR]
    >>> ctx = {"trusted_source": True}
    >>> validate(user, ctx=ctx)  # PASS; validation skipped

All validation hooks have access to context object via ``ctx`` argument. See
:mod:`modelity.hooks` for more information.

Accessing entire model tree during validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each validator can access root model via dedicated ``root`` argument. The root
model is the one for which :func:`modelity.helpers.validate` was originally
called and is passed to all validators, including ones in nested models. This
gives the possibility to access any part of the model tree from any validator
and it allows to perform complex cross-field, or cross-model verifications at
the cost of making nested models aware of where those are used in.

Here's an example:

.. testcode::

    from modelity.api import Model, UserError, field_validator, ValidationError

    class Address(Model):
        city: str
        postal_code: str

        @field_validator("postal_code")
        def _validate_postal_code(self, root: Model, value: str):
            # Access root model to validate based on other fields
            if isinstance(root, User) and root.country == "US":
                if not value.isdigit() or len(value) != 5:
                    raise UserError("US postal code must be 5 digits")

    class User(Model):
        name: str
        country: str
        address: Address

.. doctest::

    >>> user = User(name="John", country="US", address=Address(city="NYC", postal_code="1000X"))
    >>> from modelity.api import validate
    >>> validate(user)  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: ...
    >>> user = User(name="John", country="US", address=Address(city="NYC", postal_code="10001"))
    >>> validate(user)
    >>> user.address.postal_code
    '10001'

.. tip::

    Similar behavior can be achieved from the root model when
    :func:`modelity.hooks.location_validator` is used. However, the cost of
    using location validators is higher as those are dynamically matched to
    model locations during validation and cannot be precomputed.

Registering custom types
------------------------

Introducing **type handlers**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity implements parsing mechanism via so called **type handlers**. These
are subclasses of :class:`modelity.base.TypeHandler` abstract base class that
need to implement two mandatory methods:

* ``parse`` (with type parsing logic),
* and ``accept`` (with visitor accepting logic).

This mechanism is used by Modelity during compilation of type annotations which
is done shortly after model declaration ends (not in runtime!). Modelity does
that in recursive way. For example, for ``list[int]`` type following actions
take place to build needed type handler:

1. Find type handler for ``list`` type.
2. Find type handler for ``int`` type.
3. Build ``list[int]`` type handler from handlers found in previous steps.
4. Use created type handler for field annotated with ``list[int]``.

If needed type could not be found, :exc:`modelity.exc.UnsupportedTypeError`
exception is raised, preventing the model type from being successfully created
and giving instant feedback for the user.

First custom type handler
^^^^^^^^^^^^^^^^^^^^^^^^^

Let's assume we have following type defined:

.. testcode::

    import dataclasses

    @dataclasses.dataclass
    class Vec2D:
        x: float
        y: float

Let's now try to use it as a type of Modelity model:

.. doctest::

    >>> from modelity.api import Model
    >>> class Object(Model):
    ...     position: Vec2D
    ...     direction: Vec2D
    Traceback (most recent call last):
      ...
    modelity.exc.UnsupportedTypeError: unsupported type used: <class 'Vec2D'>

As you can see, Modelity cannot handle our new type out of the box and it
reports :exc:`modelity.exc.UnsupportedTypeError` exception when model is
declared. To fix that, we need to create type handler for our **Vec2D** type
introduced earlier. This is a simplified version of how such type handler could
look like:

.. testcode::

    from typing import Any

    from modelity.api import TypeHandler, Loc, Error, ModelVisitor, ErrorFactory, Unset, UnsetType

    class Vec2DTypeHandler(TypeHandler):

        def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
            if isinstance(value, Vec2D):
                return value  # No conversion needed
            if not isinstance(value, tuple) or len(value) != 2:
                errors.append(ErrorFactory.invalid_type(loc, value, [Vec2D]))
                return Unset
            return Vec2D(*value)  # Convert a 2-dimensional tuple

        def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
            visitor.visit_any(loc, value)  # Calls most generic visitor method

Now, the newly created type handler must be registered in Modelity. To do that
you need to use :func:`modelity.base.register_type_handler_factory` function:

.. doctest::

    >>> from modelity.api import register_type_handler_factory
    >>> register_type_handler_factory(Vec2D, lambda typ, **opts: Vec2DTypeHandler())

And now we can successfully declare our model:

.. testcode::

    from modelity.api import Model

    class Object(Model):
        position: Vec2D
        direction: Vec2D

.. doctest::

    >>> car = Object(position=(0, 0), direction=(0, 1))
    >>> car
    Object(position=Vec2D(x=0, y=0), direction=Vec2D(x=0, y=1))

And since now Modelity knows the new type, it also implicitly knows how to
handle it when used with other known types, especially containers:

.. testcode::

    from modelity.api import Model

    class ObjectCollection(Model):
        objects: list[Object]

.. doctest::

    >>> collection = ObjectCollection(objects=[])
    >>> collection.objects.append(car)  # OK
    >>> collection.objects.append({"position": (2, 3), "direction": (4, 5)})  # OK; parsing needed
    >>> collection.objects
    [Object(position=Vec2D(x=0, y=0), direction=Vec2D(x=0, y=1)), Object(position=Vec2D(x=2, y=3), direction=Vec2D(x=4, y=5))]

Using built-in type handler from custom type handler
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's once again recall **Vec2D** introduced earlier:

.. testcode::

    import dataclasses

    @dataclasses.dataclass
    class Vec2D:
        x: float
        y: float

It has ``x`` and ``y`` float fields, but our previous type handler was not
implemented with float parsing in mind, so following will be parsed
successfully, but the type will not be coerced:

.. doctest::

    >>> obj = Object(position=("2", "3"), direction=("4", "5"))
    >>> obj.position
    Vec2D(x='2', y='3')
    >>> obj.direction
    Vec2D(x='4', y='5')

To fix that, we need to use type handler for **float** type while parsing our
own **Vec2D** type. The following full example shows how this can be
accomplished:

.. testcode::

    from typing import Any

    from modelity.api import (
        TypeHandler, Loc, Error, ModelVisitor, ErrorFactory, Unset, UnsetType,
        register_type_handler_factory, create_type_handler
    )

    class Vec2DTypeHandler(TypeHandler):
        """Type handler for ``Vec2D`` type."""

        def __init__(self):
            self._float_type_handler = create_type_handler(float)  # Obtain type handler for `float` type

        def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
            if isinstance(value, Vec2D):
                return value  # No conversion needed
            if not isinstance(value, tuple) or len(value) != 2:
                errors.append(ErrorFactory.invalid_type(loc, value, [Vec2D]))
                return Unset
            x = self._float_type_handler.parse(errors, loc + Loc('x'), value[0])  # Invoke Modelity built-in float conversion
            y = self._float_type_handler.parse(errors, loc + Loc('y'), value[1])  # Same here
            return Vec2D(x, y)  # Use converted values

        def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
            visitor.visit_any(loc, value)  # Calls most generic visitor method

    # Overwrite previous type handler for `Vec2D`
    register_type_handler_factory(Vec2D, lambda typ, **opts: Vec2DTypeHandler())

    # Now declare model that uses `Vec2D`
    class Object(Model):
        position: Vec2D
        direction: Vec2D

And now let's see this in action:

.. doctest::

    >>> obj = Object(position=("2", "3"), direction=("4", "5"))
    >>> obj.position  # This is now converted to float
    Vec2D(x=2.0, y=3.0)
    >>> obj.direction
    Vec2D(x=4.0, y=5.0)

As you can see, both the input tuple and coordinates are now converted.
Moreover, since we've reused float parser, we have also implicitly implemented
error handling if coordinates are incorrect:

.. doctest::

    >>> obj.position = ("ka", "boom")
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 2 parsing errors for type 'Object':
      position.x:
        Not a valid float value [code=modelity.PARSE_ERROR, value_type=str, expected_type=float]
      position.y:
        Not a valid float value [code=modelity.PARSE_ERROR, value_type=str, expected_type=float]

Hook inheritance
----------------

Declaring base model with common hooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When using hooks you will declare hook directly in the model class for most
cases. However, sometimes same hook needs to be provided for other models as
well. Consider this example:

.. testcode::

    from modelity.base import Model
    from modelity.hooks import field_preprocessor

    class First(Model):
        foo: str

        @field_preprocessor("foo")
        def _strip_string(value):
            if isinstance(value, str):
                return value.strip()
            return value

    class Second(Model):
        bar: str

        @field_preprocessor("bar")
        def _strip_string(value):  # duplicated!
            if isinstance(value, str):
                return value.strip()
            return value

We have two models that need some preprocessing logic for string inputs to get
rid of white characters. The example from above duplicates same functionality,
but works just fine from the model user's PoV:

.. doctest::

    >>> first = First(foo=" 123")
    >>> second = Second(bar="456 ")
    >>> first.foo
    '123'
    >>> second.bar
    '456'

However, this is not an elegant solution, as the example break DRY principle.
Let's modify it a bit and extract logic to a separate helper function:

.. testcode::

    from modelity.base import Model
    from modelity.hooks import field_preprocessor

    def _strip_string(value):
        if isinstance(value, str):
            return value.strip()
        return value

    class First(Model):
        foo: str

        @field_preprocessor("foo")
        def _strip_string(value):
            return _strip_string(value)

    class Second(Model):
        bar: str

        @field_preprocessor("bar")
        def _strip_string(value):  # duplicated!
            return _strip_string(value)

Now it is slightly better, and the functionality is still the same:

.. doctest::

    >>> first = First(foo=" 123")
    >>> second = Second(bar="456 ")
    >>> first.foo
    '123'
    >>> second.bar
    '456'

However, we still need to remember to add 3 additional lines to each single
model that will need such stripping functionality. The best solution for that
is to create a common base class and declare stripping hook **inside base
class**. After further refactoring, the code looks as follows:

.. testcode::

    from modelity.base import Model
    from modelity.hooks import field_preprocessor


    class Base(Model):

        @field_preprocessor()  # use this hook for any field...
        def _strip_string(value):  # ...especially if we don't use it for any particular field
            if isinstance(value, str):
                return value.strip()
            return value


    class First(Base):
        foo: str


    class Second(Base):
        bar: str


    class Third(Base):  # Just one more class to automatically reuse stripping logic
        baz: str

And let's check this in practice once again:

.. doctest::

    >>> first = First(foo=" 123")
    >>> second = Second(bar="456 ")
    >>> third = Third(baz=" 789 ")
    >>> first.foo, second.bar, third.baz
    ('123', '456', '789')

Using mixin classes with hooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 0.24.0

Sometimes having all the hooks in a single common base class, or even several
separate base classes, is too rigid and forces you to inherit from base class
even if the model is logically not a subclass of such base. To resolve such
issues, Modelity now provides an easy way to declare hooks inside non-model
mixin classes that can then be mixed in to any model you want.

Let's slightly extend an example from above to see how to use mixins:

.. testcode::

    from modelity.api import Model, Deferred, field_preprocessor


    class StringStrippingMixin:  # this is a mixin; we don't inherit from model

        @field_preprocessor()  # use this hook for any field...
        def _strip_string(value):  # ...especially if we don't use it for any particular field
            if isinstance(value, str):
                return value.strip()
            return value


    class Base(Model, StringStrippingMixin):  # base class for First and Second; both will use the mixin
        pass


    class First(Base):
        foo: Deferred[str]


    class Second(Base):
        bar: Deferred[str]


    class Third(Model):  # Here we don't use our mixin...
        baz: Deferred[str]


    class Fourth(Third, StringStrippingMixin):  # ...and here we do
        spam: Deferred[str]

And the final check looks as follows:

.. doctest::

    >>> first = First(foo=" 123")
    >>> second = Second(bar="456 ")
    >>> third = Third(baz=" 789 ")
    >>> fourth = Fourth(spam=' spam ')
    >>> first.foo, second.bar, third.baz, fourth.spam
    ('123', '456', ' 789 ', 'spam')
