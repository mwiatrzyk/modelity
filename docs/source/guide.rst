.. _guide:

User's guide
============

Declaring fields with default values
------------------------------------

Modelity provides 3 ways of declaring field that has default value:

.. testcode::

    from modelity.model import Model, FieldInfo

    class First(Model):
        foo: int = 1

    class Second(Model):
        foo: int = FieldInfo(default="2")  # <-- this will be parsed

    class Third(Model):
        foo: int = FieldInfo(default_factory=lambda: 'not an int')  # <-- this will fail unless shadowed by other value

Default values are used only when model is constructed and only if there no
other values given. For example:

.. doctest::

    >>> First()  # <-- here the default value will be used
    First(foo=1)
    >>> First(foo=111)  # <-- here the default value is ignored
    First(foo=111)

For Modelity, default value is no different from the value provided by the user
and as such it is normally parsed like any other:

.. doctest::

    >>> Second()
    Second(foo=2)

As a drawback, it will not be possible to create model if default value cannot
be parsed:

.. doctest::

    >>> Third()
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'Third' with 1 error(-s):
      foo:
        could not parse value as integer number [code=modelity.PARSING_ERROR, value_type=<class 'str'>]

The error, however, will not happen if another, valid value will be given:

.. doctest::

    >>> Third(foo=333)
    Third(foo=333)

Using collection types
----------------------

The **tuple** type
^^^^^^^^^^^^^^^^^^

Modelity supports 3 variants of :class:`tuple` type:

* **untyped** tuple (i.e. just :class:`tuple` with no extra types),
* **typed, fixed-size** tuple (f.e. ``tuple[int, str]``),
* **typed, unlimited size** tuple (f.e. ``tuple[int, ...]``).

Let's use all in the example model to see how it works:

.. testcode::

    from modelity.model import Model

    class TupleExample(Model):
        untyped: tuple
        fixed: tuple[int, str]
        unlimited: tuple[int, ...]

For **untyped** tuple, the field can be initialized with tuple or sequence of
any size and containing any items:

.. doctest::

    >>> example = TupleExample()
    >>> example.untyped = [1, "foo", 3.14]
    >>> example.untyped
    (1, 'foo', 3.14)

For **typed, fixed-size** tuple the input must contain exact number of items
and each item must have valid or convertible value, compatible with the type at
corresponding index:

.. doctest::

    >>> example.fixed = [123]  # incorrect, missing second item
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'TupleExample' with 1 error(-s):
      fixed:
        invalid tuple format; expected format: <class 'int'>, <class 'str'> [code=modelity.INVALID_TUPLE_FORMAT, value_type=<class 'list'>]

.. doctest::

    >>> example.fixed = [123, "spam", "more spam"]  # incorrect, too many items
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'TupleExample' with 1 error(-s):
      fixed:
        invalid tuple format; expected format: <class 'int'>, <class 'str'> [code=modelity.INVALID_TUPLE_FORMAT, value_type=<class 'list'>]

.. doctest::

    >>> example.fixed = [123, 123]  # incorrect, second item must be string
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'TupleExample' with 1 error(-s):
      fixed.1:
        string value required [code=modelity.UNSUPPORTED_VALUE_TYPE, value_type=<class 'int'>]

.. doctest::

    >>> example.fixed = ["1", "2"]  # correct; first item is convertible to int
    >>> example.fixed
    (1, '2')

Finally, for **typed, unlimited size** tuple the size of a tuple does not
matter, but all items must be of the same type, or be convertible to that type:

.. doctest::

    >>> example.unlimited = [1, 2, "spam"]
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'TupleExample' with 1 error(-s):
      unlimited.2:
        could not parse value as integer number [code=modelity.PARSING_ERROR, value_type=<class 'str'>]

.. doctest::

    >>> example.unlimited = []
    >>> example.unlimited
    ()

.. doctest::

    >>> example.unlimited = [1, 2, "3", 4]
    >>> example.unlimited
    (1, 2, 3, 4)

The **list** type
^^^^^^^^^^^^^^^^^

Modelity supports both **typed** and **untyped** lists. Check the example
below:

.. testcode::

    from modelity.model import Model

    class ListExample(Model):
        untyped: list
        typed: list[int]

The **untyped** list fields accept lists or sequences (other than :class:`str`
and :class:`bytes`) containing anything:

.. doctest::

    >>> example = ListExample()
    >>> example.untyped = (1, 2, "spam", 3.14)
    >>> example.untyped
    [1, 2, 'spam', 3.14]

On the other hand, **typed** list will only accept input if all items have
valid type:

.. doctest::

    >>> example.typed = [1, 2, "42", "spam"]
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'ListExample' with 1 error(-s):
      typed.3:
        could not parse value as integer number [code=modelity.PARSING_ERROR, value_type=<class 'str'>]

.. doctest::

    >>> example.typed = [1, 2, "42"]
    >>> example.typed
    [1, 2, 42]

Modelity uses proxies for mutable typed containers. This allows to intercept
calls to mutating methods, like :meth:`list.append` or :meth:`list.extend`, and
to check if given input has valid type. Thanks to this feature, the model
integrity is preserved all the time. This is one of Modelity core features.
Check the example below:

.. doctest::

    >>> example.typed.append("123")
    >>> example.typed
    [1, 2, 42, 123]

Despite the fact, that ``"123"`` string was appended, Modelity has
automatically converted it to the desired type. And, of course, if incorrect
type is given, then exception will be raised:

.. doctest::

    >>> example.typed.append("not an int")
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'list' with 1 error(-s):
      4:
        could not parse value as integer number [code=modelity.PARSING_ERROR, value_type=<class 'str'>]

The other mutating methods will also behave like this, as **typed** lists are
wrapped with a proxy that is a subclass of
:class:`collections.abc.MutableSequence` base class.

The **dict** type
^^^^^^^^^^^^^^^^^

Modelity supports both **untyped** and **typed** dicts:

.. testcode::

    from modelity.model import Model

    class DictExample(Model):
        untyped: dict
        typed: dict[str, int]

The **untyped** dict field will accept mappings containing anything:

.. doctest::

    >>> example = DictExample()
    >>> example.untyped = {1: "one", "two": 2, None: 3.14}
    >>> example.untyped
    {1: 'one', 'two': 2, None: 3.14}

The **typed** dict field will only accept input mapping if its keys and values
have correct types or its keys and values can be parsed to correct types. In
the model defined above, the dict needs :class:`str` as keys, and :class:`int`
as values:

.. doctest::

    >>> example = DictExample()
    >>> example.typed = {"one": 1, "two": "2", "three": "3"}
    >>> example.typed
    {'one': 1, 'two': 2, 'three': 3}

The parsing will fail if either key is invalid:

.. doctest::

    >>> example.typed = {1: 1}
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'DictExample' with 1 error(-s):
      typed:
        string value required [code=modelity.UNSUPPORTED_VALUE_TYPE, value_type=<class 'int'>]

Or if value is invalid:

.. doctest::

    >>> example.typed = {"one": "one"}
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'DictExample' with 1 error(-s):
      typed.one:
        could not parse value as integer number [code=modelity.PARSING_ERROR, value_type=<class 'str'>]

Typed dict fields can later be modified with type parsing being performed by
Modelity underneath:

.. doctest::

    >>> example = DictExample(typed={})
    >>> example.typed["one"] = "1"
    >>> example.typed
    {'one': 1}
    >>> example.typed.update({"two": "2"})
    >>> example.typed
    {'one': 1, 'two': 2}

These mutating methods will fail if incorrect key or value is given. For
example:

.. doctest::

    >>> example.typed["one"] = "one"
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'dict' with 1 error(-s):
      one:
        could not parse value as integer number [code=modelity.PARSING_ERROR, value_type=<class 'str'>]

The other mutating methods will also behave like this, as **typed** dicts are
wrapped with a proxy that is a subclass of
:class:`collections.abc.MutableMapping` base class.

The **set** type
^^^^^^^^^^^^^^^^

Modelity supports both **untyped** and **typed** sets:

.. testcode::

    from modelity.model import Model

    class SetExample(Model):
        untyped: set
        typed: set[int]

The **untyped** set allows any kind of sequence (other than :class:`str` and
:class:`bytes` instances) to be converted to the :class:`set` object:

.. doctest::

    >>> example = SetExample()
    >>> example.untyped = [1, 2, 2, 3, "foo", "spam", "foo"]
    >>> example.untyped == {1, 2, 3, "foo", "spam"}
    True

Since we convert to set, any duplicates are removed, as in the example above.

The **typed** set, on the other hand, besides converting given sequences to the
:class:`set` object does also perform type parsing of each item, to
:class:`int` object in this case:

.. doctest::

    >>> example = SetExample()
    >>> example.typed = [1, "2", 2, "1"]
    >>> example.typed == {1, 2}
    True

Typed sets, just like typed lists and dicts, allow modifications of the field
after it was initialized with automatic type parsing:

.. doctest::

    >>> example = SetExample(typed=[])
    >>> example.typed.add("1")
    >>> example.typed == {1}
    True
    >>> example.typed |= [1, 2]
    >>> example.typed |= ["spam"]
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'set' with 1 error(-s):
      (empty):
        could not parse value as integer number [code=modelity.PARSING_ERROR, value_type=<class 'str'>]

The other mutating methods will also behave like this, as **typed** sets are
wrapped with a proxy that is a subclass of
:class:`collections.abc.MutableSet` base class.

Using nested models
-------------------

Modelity allows nesting models inside another models. For example, the model
**Address** can be used both by model **Person** and by model **Company**:

.. testcode::

    import typing
    import datetime

    from modelity.model import Model
    from modelity.constraints import Regex

    class Address(Model):
        address_line1: str
        address_line2: typing.Optional[str]
        city: str
        state_province: typing.Optional[str]
        postal_code: str
        country_code: typing.Annotated[str, Regex(r"^[A-Z]{2}$")]

    class Person(Model):
        name: str
        surname: str
        dob: datetime.date
        home_address: Address

    class Company(Model):
        name: str
        description: str
        office_address: Address

Nested models can only be initialized with instances of that model:

.. doctest::

    >>> john = Person(name="John", surname="Doe")
    >>> john.home_address = Address(
    ...     address_line1="123 Maple Street",
    ...     city="Springfield",
    ...     state_province="IL",
    ...     postal_code="62704",
    ...     country_code="US"
    ... )
    >>> john.home_address
    Address(address_line1='123 Maple Street', address_line2=Unset, city='Springfield', state_province='IL', postal_code='62704', country_code='US')

Or with mappings that will be parsed into instances of that model:

.. doctest::

    >>> company = Company(name="Fictional Company Ltd.")
    >>> company.office_address = {'city': 'Springfield'}
    >>> company.office_address
    Address(address_line1=Unset, address_line2=Unset, city='Springfield', state_province=Unset, postal_code=Unset, country_code=Unset)

Such nested models are automatically serialized when
:func:`modelity.model.dump` is used:

.. doctest::

    >>> from modelity.model import dump
    >>> dump(john, exclude_unset=True)
    {'name': 'John', 'surname': 'Doe', 'home_address': {'address_line1': '123 Maple Street', 'city': 'Springfield', 'state_province': 'IL', 'postal_code': '62704', 'country_code': 'US'}}
    >>> dump(company, exclude_unset=True)
    {'name': 'Fictional Company Ltd.', 'office_address': {'city': 'Springfield'}}

Nested models, as being a part of parent model, are also automatically
validated when :meth:`modelity.model.validate` is used on the parent model:

.. doctest::

    >>> from modelity.model import validate
    >>> validate(company)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'Company' failed with 4 error(-s):
      description:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      office_address.address_line1:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      office_address.country_code:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      office_address.postal_code:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]

In this last example there were 4 validation errors found, as there was
required field *description* missing in the **Company** model, and the
remaining 3 errors were caused by unsatisfied **Address** model requirements.

Constraining fields with **typing.Annotated**
---------------------------------------------

Modelity has its own support for :obj:`typing.Annotated` typing form, backed up
with :mod:`modelity.constraints` module, or using user-defined constraints that
satisfy the :class:`modelity.interface.IConstraint` protocol. This can
be used to create field-level validations like length or range checking. See
this in action:

.. testcode::

    import typing

    from modelity.model import Model
    from modelity.constraints import Ge, Le

    class AnnotatedExample(Model):
        foo: typing.Annotated[int, Ge(0), Le(100)]

In the example above, we've created field *foo* of type :class:`int` that must
be from the [0, 100] range. Now let's see what will happen if the value is less
than 0:

.. doctest::

    >>> m = AnnotatedExample()
    >>> m.foo = -1
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'AnnotatedExample' with 1 error(-s):
      foo:
        the value must be >= 0 [code=modelity.CONSTRAINT_FAILED, value_type=<class 'int'>]

The constraint fails, and it fails at the parsing stage, because checking
constraints is done during parsing, as such defined constraints are
field-specific and cannot rely on other fields. The error will not be reported
if any value within allowed range is given:

.. doctest::

    >>> m.foo = 100
    >>> m.foo
    100

Although the constraints are check at the parsing stage, some field types can
be modified later and that can lead to breaking the constraint. This can happen
when constraining a mutable container. For example:

.. testcode::

    import typing

    from modelity.model import Model
    from modelity.constraints import MaxLen

    class AnnotatedList(Model):
        items: typing.Annotated[list[int], MaxLen(4)]

Now, let's create a valid instance:

.. doctest::

    >>> m = AnnotatedList(items=[1, 2, 3, 4])
    >>> m.items
    [1, 2, 3, 4]

And now let's break it by adding one more item:

.. doctest::

    >>> m.items.append(5)
    >>> m.items
    [1, 2, 3, 4, 5]

Since the field was already initialized, modifying it will not trigger the
constraint. However, all constraints are automatically verified again at the
validation stage, so such model will now fail validation:

.. doctest::

    >>> from modelity.model import validate
    >>> validate(m)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'AnnotatedList' failed with 1 error(-s):
      items:
        the value is too long; maximum length is 4 [code=modelity.CONSTRAINT_FAILED, data={'max_len': 4}]

.. note::

    The constraints are always executed at the validation stage, no matter if the
    field is mutable or not. The only difference is that immutable fields can only
    be modified by assigning with a different value (thus invoking parsing
    stage), while mutable can be modified "in-place", with no need to re-assign
    to a different value.

Customizing models with user-defined hooks
------------------------------------------

The **field preprocessing** hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create field preprocessor, :func:`modelity.model.field_preprocessor`
decorator must be used.

Field preprocessors allow embedding custom function into the :term:`data parsing<Data parsing>`
stage before type coercing takes place. Thanks to this it is possible to
perform filtering of the input data on per-field basis to avoid later type
parsing errors. For example, a preprocessor for stripping input value from
white characters may be created like this:

.. testcode::

    from modelity.model import Model, field_preprocessor

    class FieldPreprocessorExample(Model):
        foo: str
        bar: str

        @field_preprocessor("bar")  # (1)
        def _strip(value):  # (2)
            if isinstance(value, str):  # (3)
                return value.strip()
            return value

The user-defined preprocessor is declared only for *bar* field (1), therefore
only *bar* field will be stripped from the white characters:

.. doctest::

    >>> example = FieldPreprocessorExample()
    >>> example.foo = "\t spam\n"
    >>> example.foo
    '\t spam\n'
    >>> example.bar = "\t spam\n"
    >>> example.bar
    'spam'

Preprocessing hooks, as executed before data parsing, can get called with
values of any type, therefore :func:`isinstance` checks like in (3) will be
frequently used to avoid exceptions or unwanted alternations of the input data.

.. important::

    In the example above, at (2), the function *_strip* was declared with
    single argument *value* to get the value the field was initialized with.
    There are actually several other argument names with their special
    meaning. Please proceed to :class:`modelity.interface.IFieldPreprocessingHook`
    class documentation for more details on this topic.

The **field postprocessing** hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

General information
~~~~~~~~~~~~~~~~~~~

Postprocessors are the last step of data parsing pipeline and are executed only
when successful preprocessing and type parsing took place earlier.
Postprocessors work on a per-field basis, but unlike preprocessors they do have
an access to model's instance via `self` argument (if defined). The return
value of a field preprocessor is either passed to a next preprocessor (if more
than one are defined) or set inside a model as a final value for a field. To
declare a postprocessor, :func:`modelity.model.field_postprocessor` decorator
must be used.

Now let's take a dive into possible use cases.

Example 1: Data normalization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Postprocessors known the type of the value they receive from previous parsing
steps, therefore they can further process it:

.. testcode::

    import math

    from modelity.model import Model, field_postprocessor

    class Vec2d(Model):
        x: float
        y: float

        def length(self):
            return math.sqrt(self.x**2 + self.y**2)

        def normalize(self):
            l = self.length()
            return Vec2d(x=self.x / l, y=self.y / l)

    class Car(Model):
        direction: Vec2d

        @field_postprocessor("direction")
        def _normalize_vector(value: Vec2d):
            return value.normalize()

In the example above, we want `direction` attribute of a `Car` model to always
contain normalized vector. And now, since the postprocessor was assigned, any
time a direction is set to a valid value, the postprocessor will execute and
return normalized vector instead of original one.

Now, let's check how this works:

.. doctest::

    >>> car = Car()
    >>> car.direction = Vec2d(x=2, y=2)
    >>> car.direction
    Vec2d(x=0.7071067811865475, y=0.7071067811865475)

Example 2: Nested model validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can also use field postprocessors for running model validation using
:func:`modelity.model.validate` function if we need to enforce initialization
with valid objects only. In the previous example everything works fine until an
incomplete vector is given:

.. doctest::

    >>> car.direction = Vec2d(x=3)
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'Car' with 1 error(-s):
      direction:
        unsupported operand type(s) for ** or pow(): 'UnsetType' and 'int' [code=modelity.EXCEPTION, value_type=<class 'modelity.unset.UnsetType'>]

To avoid such errors, let's extend the example by validating the vector before
normalization:

.. testcode::

    import math

    from modelity.model import Model, field_postprocessor, validate

    class Vec2d(Model):
        x: float
        y: float

        def length(self):
            return math.sqrt(self.x**2 + self.y**2)

        def normalize(self):
            l = self.length()
            return Vec2d(x=self.x / l, y=self.y / l)

    class Car(Model):
        direction: Vec2d

        @field_postprocessor("direction")
        def _normalize_vector(value: Vec2d):
            validate(value)
            return value.normalize()

And now, there is an explicit error showing that the vector has required field
missing:

.. doctest::

    >>> car = Car()
    >>> car.direction = Vec2d(x=3)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'Vec2d' failed with 1 error(-s):
      y:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]

This example shows that validation, although optional as requiring explicit
:func:`modelity.model.validate` function call, can be made required and run
automatically when needed.

Example 3: Reading from/writing to other model's fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 0.15.0

Postprocessors can access model object they are declared in to either perform
cross field validation (simple cases only), or to write to other fields.

.. important::

    The way how this works strongly depends on field ordering. Modelity
    processes fields in their declaration order, so fields one wants to read
    from or write to should be declared BEFORE the field that uses this
    functionality. Otherwise, the field may not have value yet (when reading),
    or value set (when writing) will not be permanent.

For example, we can use this feature to check if repeated password is correct:

.. testcode::

    class Account(Model):
        login: str
        repeated_password: str  # NOTE: Must be declared BEFORE password to work
        password: str

        @field_postprocessor("password")
        def _compare_with_repeated(self, value):
            if value != self.repeated_password:
                raise TypeError("the passwords don't match")
            return value

.. doctest::

    >>> account = Account(login="foo", password="p@ssword", repeated_password="p@ssword")  # OK
    >>> account
    Account(login='foo', repeated_password='p@ssword', password='p@ssword')

.. doctest::

    >>> Account(login="foo", password="p@ssword")  # NOK, `repeated_password`` is missing
    Traceback (most recent call last):
        ...
    modelity.exc.ParsingError: parsing failed for type 'Account' with 1 error(-s):
      password:
        the passwords don't match [code=modelity.EXCEPTION, value_type=<class 'modelity.unset.UnsetType'>]

.. doctest::

    >>> Account(login="foo", password="p@ssword", repeated_password='password')  # NOK, `repeated_password` is not the same
    Traceback (most recent call last):
        ...
    modelity.exc.ParsingError: parsing failed for type 'Account' with 1 error(-s):
      password:
        the passwords don't match [code=modelity.EXCEPTION, value_type=<class 'modelity.unset.UnsetType'>]

Another example shows how to write to other field when a given field is set or
modified. This can be used to update model's modification time or to perform
other similar things:

.. testcode::

    from modelity.unset import Unset

    class InMemoryFile(Model):
        modified: int  # this is just for easier testing; with datetime it would work in exactly the same way
        created: int
        name: str
        data: bytes

        @field_postprocessor("created")
        def _set_modified(self, value):
            self.modified = value  # sets `modified` to same value when `created` is changed
            return value

        @field_postprocessor("name", "data")
        def _update_modified(self, value):
            self.modified += 1
            return value

.. doctest::

    >>> file = InMemoryFile(created=1)
    >>> file.created
    1
    >>> file.modified  # was set implicitly by postprocessor
    1
    >>> file.name = "spam.txt"
    >>> file.data = b"content of spam.txt"
    >>> file.created
    1
    >>> file.modified  # was incremented when `name` and `data` were set
    3

.. important::

    Please remember to always return a value from postprocessor, or otherwise
    fields will be set to ``None``. There are no more checks after
    postprocessing stage, so it is quite easy to break model's integrity if
    return value is missing or wrong return value was used.

.. _model_prevalidator:

The **model_prevalidator** hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create model prevalidator, :func:`modelity.model.model_prevalidator`
decorator must be used.

This hook is executed during validation, for the model it was declared in, and
**before** any other validators. Model prevalidator can access entire model,
even if defined for the nested model. Here's an example:

.. testcode::

    from modelity.model import Model, model_prevalidator, validate

    class Outer(Model):

        class Inner(Model):
            foo: int

            @model_prevalidator()
            def _prevalidate_inner(root):  # (1)
                if root.should_fail:  # Here we check if root model has 'should_fail' field set to True
                    raise ValueError("failing validation, as should_fail=True")

        should_fail: bool = False
        inner: Inner

Although this is an artificial example, it shows the possibility to access root
model's fields from nested model's instances:

.. doctest::

    >>> outer = Outer()
    >>> outer.inner = {"foo": "123"}
    >>> outer
    Outer(should_fail=False, inner=Outer.Inner(foo=123))
    >>> validate(outer)  # This will pass
    >>> outer.should_fail = True
    >>> validate(outer)  # This will fail now
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'Outer' failed with 1 error(-s):
      inner:
        failing validation, as should_fail=True [code=modelity.EXCEPTION, data={'exc_type': <class 'ValueError'>}]

.. note::

    In the example above, method ``_prevalidate_inner`` was declared with just
    *root* argument, which contains reference to the model for which
    :func:`modelity.model.validate` function was called. In Modelity, all
    decorators have predefined set of arguments with their specific meaning,
    type and usage. Check
    :meth:`modelity.interface.IModelValidationHook.__call__` to get the list of
    all available arguments.

The **model_postvalidator** hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create model postvalidator, :func:`modelity.model.model_postvalidator` decorator
must be used.

Model postvalidators, unlike :ref:`prevalidators<model_prevalidator>` from the previous
section, are executed **after** all other validator. That's the only
difference, as the interface for both is the same.

Since this validator is executed after any other validators, we can use it, for
example, to control the number of validation errors the model can produce:

.. testcode::

    from modelity.model import Model, model_postvalidator, validate

    class ModelPostvalidatorExample(Model):
        foo: int
        bar: int
        baz: int
        clean_errors: bool = False  # (1)

        @model_postvalidator()
        def _clean_errors_if_flag_set(self, errors):
            if self.clean_errors:
                errors.clear()

In the example above, we have 3 required fields and a flag (1) that can, during
model postvalidation, remove all errors found so far. And since model
postvalidator runs **after** all other validators, we can use it to erase
errors that were found earlier.

By default, the validation works as usual:

.. doctest::

    >>> outer = ModelPostvalidatorExample()
    >>> validate(outer)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'ModelPostvalidatorExample' failed with 3 error(-s):
      bar:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      baz:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      foo:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]

But when *clean_errors* flag is set to ``True``, then all validation
errors will be removed by model postvalidator:

.. doctest::

    >>> outer.clean_errors = True
    >>> validate(outer)

The **field_validator** hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To declare model method as field validator, it has to be decorated with
:func:`modelity.model.field_validator` decorator.

Field validators, just like model pre- and postvalidators, are executed when
model is validated, but only for fields they are declared for, and only if the
field has value set. Here's an example:

.. testcode::

    from modelity.model import Model, field_validator, validate

    class UserAccount(Model):
        username: str
        password: str
        repeated_password: str

        @field_validator("repeated_password")
        def _compare_with_password(self, value):
            if self.password != value:
                raise ValueError("passwords don't match")

If we now create empty **UserAccount** instance and validate it, custom
validator will not be called, as no value was assigned:

.. doctest::

    >>> account = UserAccount()
    >>> validate(account)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'UserAccount' failed with 3 error(-s):
      password:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      repeated_password:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      username:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]

But if now we give it a value, it will try to compare it with *password* field
and will fail with custom error:

.. doctest::

    >>> account.repeated_password = "p@55w0rd"
    >>> validate(account)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'UserAccount' failed with 3 error(-s):
      password:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      repeated_password:
        passwords don't match [code=modelity.EXCEPTION, data={'exc_type': <class 'ValueError'>}]
      username:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]

Finally, if model is valid, no errors will be reported:

.. doctest::

    >>> account.username = "dummy"
    >>> account.password = "p@55w0rd"
    >>> validate(account)

Using custom types
------------------

Let's define custom type:

.. testcode::

    import dataclasses

    @dataclasses.dataclass
    class Point:
        x: float
        y: float

Such type cannot be used by Modelity out of the box, as it is defined outside
of Modelity type system. Trying to use it will raise
:exc:`modelity.exc.UnsupportedTypeError` exception:

.. testcode::

    from modelity.model import Model

    class CustomTypeExample(Model):
        foo: Point

.. testoutput::

    Traceback (most recent call last):
      ...
    modelity.exc.UnsupportedTypeError: unsupported type used: <class 'Point'>

To let Modelity know how to process the type we need to create
``__modelity_type_descriptor__`` static method that returns instance of
:class:`modelity.interface.ITypeDescriptor` protocol. Let's then declare class
**Point** again, but this time with Modelity type descriptor factory hook:

.. testcode::

    import dataclasses

    from modelity.error import Error

    @dataclasses.dataclass
    class Point:
        x: float
        y: float

        @staticmethod
        def __modelity_type_descriptor__(typ, make_type_descriptor, type_opts):

            class PointDescriptor:

                def parse(self, errors, loc, value):
                    if not isinstance(value, tuple) or len(value) != 2:
                        errors.append(Error(loc, "custom.INVALID_POINT", "2-element tuple is required"))
                        return
                    return typ(*(float_descriptor.parse(errors, loc, x) for x in value))

                def dump(self, loc, value, filter):
                    return (value.x, value.y)

                def validate(self, root, ctx, errors, loc, value):
                    return

            # It is possible to use Modelity built-in types for parsing floats
            # to reuse existing mechanisms.
            float_descriptor = make_type_descriptor(float, type_opts)
            return PointDescriptor()

And now, let's create the model again:

.. testcode::

    from modelity.model import Model

    class CustomTypeExample(Model):
        foo: Point

Since the new custom type parses **Point** object out of tuple, it will fail
parsing when non-tuple is given:

.. doctest::

    >>> model = CustomTypeExample()
    >>> model.foo = 123
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'CustomTypeExample' with 1 error(-s):
      foo:
        2-element tuple is required [code=custom.INVALID_POINT, value_type=<class 'modelity.unset.UnsetType'>]

But if the valid tuple was given, we get **Point** object as a result of such assignment:

.. doctest::

    >>> model.foo = (1, 2)
    >>> model
    CustomTypeExample(foo=Point(x=1.0, y=2.0))

Since it is also necessary to provide serialization and validation logic for a
new type, then following will also work fine with a new type:

.. doctest::

    >>> from modelity.model import dump, validate
    >>> dump(model)
    {'foo': (1.0, 2.0)}
    >>> validate(model)

.. _registering-3rd-party-types-label:

Registering 3rd party types
---------------------------

.. versionadded:: 0.14.0

Modelity works on a predefined set of types and any type from beyond of that
set is unknown to Modelity unless it is explicitly told how to parse, validate
and dump values of that type. In previous chapter it was presented how to enable
the handling of a new type by using ``__modelity_type_descriptor__`` hook
directly in the class definition. The other approach is to use
:func:`modelity.model.type_descriptor_factory` decorator to register a new
type. Here's how to use it:

.. testcode::

    from modelity.model import type_descriptor_factory

    @dataclasses.dataclass
    class Point:  # Let's assume this is a "3rd party" type
        x: float
        y: float

    @type_descriptor_factory(Point)
    def make_point_type_descriptor_factory(typ, make_type_descriptor, type_opts):

        class PointDescriptor:

            def parse(self, errors, loc, value):
                if not isinstance(value, tuple) or len(value) != 2:
                    errors.append(Error(loc, "custom.INVALID_POINT", "2-element tuple is required"))
                    return
                return typ(*(float_descriptor.parse(errors, loc, x) for x in value))

            def dump(self, loc, value, filter):
                return (value.x, value.y)

            def validate(self, root, ctx, errors, loc, value):
                return

        # It is possible to use Modelity built-in types for parsing floats
        # to reuse existing mechanisms.
        float_descriptor = make_type_descriptor(float, type_opts)
        return PointDescriptor()

And since now, the new type becomes visible to Modelity:

.. testcode::

    from modelity.model import Model

    class Dummy(Model):
        point: Point

.. doctest::

    >>> model = Dummy(point=(1, 2))
    >>> model
    Dummy(point=Point(x=1.0, y=2.0))

.. note::
    Please keep in mind that this decorator should be used before first
    model class is created or otherwise the type might not be visible to
    Modelity.

.. _configurable-types-label:

Configurable types
------------------

.. note::

    Modelity type system allows customizations of selected fields via special
    *type_opts* attribute of the :class:`modelity.model.FieldInfo` class. Not
    all built-in types use this, but all that does will be presented in this
    chapter.

The **bool** type
^^^^^^^^^^^^^^^^^

In Modelity, :class:`bool` type, which by default only supports boolean values,
can be extended to allow other values as a valid ``True`` or ``False``. This
can be done via following type options:

* **true_literals** - for defining constant(-s) that should evaluate to ``True``,
* **false_literals** - for defining constant(-s) that should evaluate to ``False``.

Let's consider following example:

.. testcode::

    from modelity.model import Model, FieldInfo

    class DoorLock(Model):
        locked: bool =\
            FieldInfo(
                type_opts=dict(
                    true_literals=['yes'],
                    false_literals=['no']
                )
            )

Now, the field *locked* can, in addition to boolean value, be also set to
either **yes** or **no** string value:

.. doctest::

    >>> lock = DoorLock()
    >>> lock.locked = True
    >>> lock.locked
    True
    >>> lock.locked = "no"
    >>> lock.locked
    False
    >>> lock.locked = "yes"
    >>> lock.locked
    True

The **datetime.datetime** type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For :class:`datetime.datetime` type fields, following options are available:

* **input_datetime_formats** - for setting the list of supported datetime formats,
* **output_datetime_format** - for setting the output datetime format, used for serialization.

Modelity supports Python's date/time formatting strings and brings its own
"sugar" on top of it for more user-friendly feel. Modelity built-in formats
are:

* ``YYYY`` - for a 4-digit year (f.e. 2024)
* ``MM`` - for a 2-digit month number (01 - 12)
* ``DD`` - for a 2-digit day number (01 - 31)
* ``hh`` - for a 2-digit hour (00 - 23)
* ``mm`` - for a 2-digit minute (00 - 59)
* ``ss`` - for a 2-digit second (00 - 59)
* ``ZZZZ`` - for a 5-digit timezone offset (f.e. +0200)

.. testcode::

    import datetime

    from modelity.model import Model, FieldInfo

    class Entry(Model):
        created: datetime.datetime =\
            FieldInfo(
                type_opts=dict(
                    input_datetime_formats=['MM-DD-YYYY hh:mm:ss'],
                    output_datetime_format='MM-DD-YYYY hh:mm:ss'
                )
            )

These options, if used, override Modelity defaults for that particular field,
therefore these new will become the only supported formats:

.. doctest::

    >>> entry = Entry()
    >>> entry.created = "12-31-2024 11:22:33"
    >>> entry.created
    datetime.datetime(2024, 12, 31, 11, 22, 33)

Now let's serialize the model to see that the output format was also used:

.. doctest::

    >>> from modelity.model import dump
    >>> dump(entry)
    {'created': '12-31-2024 11:22:33'}

The **datetime.date** type
^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`datetime.date` example is almost a copy-paste from previous section
regarding :class:`datetime.datetime` type. However, the options supported have
different names:

* **input_date_formats** - for setting the list of supported datetime formats,
* **output_date_format** - for setting the output datetime format, used for serialization.

Modelity supports Python's date formatting strings and brings its own "sugar"
on top of it for more user-friendly look and feel. Modelity built-in formats
are:

* ``YYYY`` - for a 4-digit year (f.e. 2024)
* ``MM`` - for a 2-digit month number (01 - 12)
* ``DD`` - for a 2-digit day number (01 - 31)

.. testcode::

    import datetime

    from modelity.model import Model, FieldInfo

    class Entry(Model):
        created: datetime.date =\
            FieldInfo(
                type_opts=dict(
                    input_date_formats=['MM-DD-YYYY'],
                    output_date_format='MM-DD-YYYY'
                )
            )

Now, let's parse date from string that matches given format:

.. doctest::

    >>> entry = Entry()
    >>> entry.created = "12-31-2024"
    >>> entry.created
    datetime.date(2024, 12, 31)

And finally, let's serialize the model to ensure that the output format was
also taken into account:

.. doctest::

    >>> from modelity.model import dump
    >>> dump(entry)
    {'created': '12-31-2024'}
