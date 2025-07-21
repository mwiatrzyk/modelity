.. _quickstart:

Quickstart
==========

Declaring models
----------------

Here's an example model created using Modelity:

.. testcode::

    import typing
    import datetime

    from modelity.model import Model

    class Person(Model):  # (1)
        name: str  # (2)
        second_name: typing.Optional[str]  # (3)
        surname: str  # (4)
        dob: datetime.date  # (5)

To create a model, one needs to inherit from :class:`modelity.model.Model` base
class (1) and declare fields and their types using Python's type annotation
mechanism.

In the example above a model **Person** was created with following fields:

* required **name** of type :class:`str` (2)
* optional **second_name** of type :class:`str` (3)
* required **surname** of type :class:`str` (4)
* and required **dob** (date of birth) of type :class:`datetime.date` (5).

Creating model instances
------------------------

To create model instance, one needs to call the constructor of created model
type. Modelity, unlike some other similar tools, does not force the presence of
required fields during model construction. This means, that it is fine to
create empty model with no arguments:

.. doctest::

    >>> empty = Person()
    >>> empty
    Person(name=Unset, second_name=Unset, surname=Unset, dob=Unset)

Modelity uses special singleton object :obj:`modelity.unset.Unset` as a default
value for fields that have no value set and it has initialized all fields with
that value.

Now, let's create another object, but this time let's set all required fields
with valid values:

.. doctest::

    >>> just_required = Person(name="John", surname="Doe", dob="2000-01-31")
    >>> just_required
    Person(name='John', second_name=Unset, surname='Doe', dob=datetime.date(2000, 1, 31))

There are 3 important things to mention:

* Modelity **only** allows initialization of fields via **named arguments**,
* The field *second_name* is still unset,
* Modelity automatically **parses** input value if its type is different than
  required by model (the *dob* field in this case)

Now, let's initialize all fields:

.. doctest::

    >>> full = Person(
    ...     name="Bridget",
    ...     second_name="Rose",
    ...     surname="Jones",
    ...     dob=datetime.date(1969, 11, 9)
    ... )
    >>> full
    Person(name='Bridget', second_name='Rose', surname='Jones', dob=datetime.date(1969, 11, 9))

And once again all fields, but with an additional argument *extra*:

.. doctest::

    >>> full_extra = Person(
    ...     name="Bridget",
    ...     second_name="Rose",
    ...     surname="Jones",
    ...     dob=datetime.date(1969, 11, 9),
    ...     extra="something extra"
    ... )
    >>> full_extra
    Person(name='Bridget', second_name='Rose', surname='Jones', dob=datetime.date(1969, 11, 9))

As you can see, now all fields are initialized and both model looks the same.
And they look the same, because both models are equal:

.. doctest::

    >>> full == full_extra
    True

During construction, Modelity ignores any extra arguments it gets in the
constructor, and only uses the ones that match field names, therefore the
argument *extra* was silently ignored.

Working with model objects
--------------------------

Setting fields
^^^^^^^^^^^^^^

Modelity models are mutable and can be modified after creation. However, the
rules from model definition still apply, so the field must be set to a value of
valid type, or to a value that can be converted to a valid type successfully:

.. doctest::

    >>> person = Person()
    >>> person.name = "John"
    >>> person
    Person(name='John', second_name=Unset, surname=Unset, dob=Unset)
    >>> person.dob = "1970-07-08"
    >>> person
    Person(name='John', second_name=Unset, surname=Unset, dob=datetime.date(1970, 7, 8))

And if the field was not set to a valid value, then
:exc:`modelity.exc.ParsingError` exception will be raised:

.. doctest::

    >>> person.second_name = 123
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'Person' with 1 error(-s):
      second_name:
        string value required [code=modelity.UNSUPPORTED_VALUE_TYPE, value_type=<class 'int'>]

.. important::

    It is recommended to always check validity of the model by running
    :func:`modelity.helpers.validate` function after modifications are done.

Clearing fields
^^^^^^^^^^^^^^^

In Modelity, fields with value can be cleared by either setting to
:obj:`modelity.unset.Unset`:

.. doctest::

    >>> from modelity.unset import Unset
    >>> person = Person()
    >>> person.name = "John"
    >>> person.surname = "Doe"
    >>> list(person)
    ['name', 'surname']
    >>> person.name = Unset  # <-- here the field 'name' is cleared
    >>> list(person)
    ['surname']

Or by deleting model's attribute using ``del`` keyword:

.. doctest::

    >>> list(person)
    ['surname']
    >>> del person.surname  # <-- here the field 'surname' is cleared
    >>> list(person)
    []

Both forms are equal and can be used interchangeably.

Printing
^^^^^^^^

Models can be printed to a self-describing form, similar to the one dataclasses
are using:

.. testcode::

    print(full)

.. testoutput::

    Person(name='Bridget', second_name='Rose', surname='Jones', dob=datetime.date(1969, 11, 9))

Checking equality
^^^^^^^^^^^^^^^^^

Two models can be compared. The models are equal if and only if:

* both are of the same type,
* both has same fields set to the same values.

.. doctest::

    >>> Person() == Person()
    True
    >>> Person(name="John") == Person()
    False
    >>> Person(name="John") == Person(name="John")
    True

Two models of different types are never equal, even if both have same fields:


.. testcode::

    from modelity.model import Model

    class One(Model):
        foo: int

    class Two(Model):
        foo: int

.. doctest::

    >>> One(foo=1) == Two(foo=1)
    False

Checking if the field is set
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To check if the field is set one needs to simply either get field's value and
check if it is same as :obj:`modelity.unset.Unset` object:

.. doctest::

    >>> from modelity.unset import Unset
    >>> jack = Person(name="Jack")
    >>> jack.name is Unset
    False
    >>> jack.second_name is Unset
    True

Listing fields that are set
^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible to iterate over fields that are set, in same order as the fields
are declared in the model:

.. doctest::

    >>> dan = Person(name="Dan", surname="Brown")
    >>> [x for x in dan]
    ['name', 'surname']
    >>> list(dan)
    ['name', 'surname']

.. note::

    If you only need to check if the model has at least one field check, then
    it is better to use :func:`modelity.model.has_fields_set` helper, as it
    will stop iterating on first field.

Data parsing vs model validation
--------------------------------

Modelity separates data processing into two distinct steps, or stages: **data
parsing** and **model validation**. Data parsing takes place when model is
either constructed or modified, and is performed for each field independently.
On the other hand, model validation is not executed automatically, but needs to
be called explicitly. Thanks to this approach it is possible to gradually fill
the model with data (for example, as the user is filling in the form in the UI)
with no need for any additional mechanism, and validate it once all the data
was entered. That's why Modelity will not complain about missing required
fields in the constructor; it simply defers this check until
:func:`modelity.helpers.validate` function is called.

Let's now see how these 2 stages work in practice.

First, let's check if the ``empty`` model created above is valid:

.. doctest::

    >>> from modelity.helpers import validate
    >>> validate(empty)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'Person' failed with 3 error(-s):
      dob:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      name:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      surname:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]

The validation failed with :exc:`modelity.exc.ValidationError` exception that
cleanly shows which required fields are missing. Let's now fill the model with
data, simulating "gradual" filling in by the user:

.. doctest::

    >>> empty.name = "Jack"
    >>> empty.surname = "Black"
    >>> empty.dob = "1999-01-31"
    >>> empty
    Person(name='Jack', second_name=Unset, surname='Black', dob=datetime.date(1999, 1, 31))

Now, the model ``empty`` is no longer empty, it has all required fields set, so
it is valid:

.. doctest::

    >>> validate(empty)

And so are the full models created earlier:

.. doctest::

    >>> validate(full)
    >>> validate(full_extra)

Parsing data from an untrusted source
-------------------------------------

Modelity provides :func:`modelity.helpers.load` helper especially designed for
loading data from an untrusted source, like JSON file or JSON object received
from API call. The helper automatically performs both stages and there are 3
possible outcomes depicted in subsections below.

Success
^^^^^^^

When parsing was successful, then valid model instance is returned:

.. doctest::

    >>> from modelity.helpers import load
    >>> untrusted_valid_data = {
    ...     "name": "Jack",
    ...     "surname": "Black",
    ...     "dob": "1999-01-31",
    ... }
    >>> person = load(Person, untrusted_valid_data)
    >>> person
    Person(name='Jack', second_name=Unset, surname='Black', dob=datetime.date(1999, 1, 31))

There is no need to additionally validate it, the user of this helper can
assume that the model returned is already valid if no exception was raised.

Failure at parsing stage
^^^^^^^^^^^^^^^^^^^^^^^^

Parsing of the data can fail at the parsing stage, when one or more fields have
incorrect or impossible to parse types:

.. doctest::

    >>> from modelity.helpers import load
    >>> untrusted_valid_data = {
    ...     "name": True,
    ...     "surname": "Black",
    ...     "dob": "not a date",
    ... }
    >>> person = load(Person, untrusted_valid_data)
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'Person' with 2 error(-s):
      dob:
        unsupported date format; supported formats: YYYY-MM-DD [code=modelity.UNSUPPORTED_DATE_FORMAT, value_type=<class 'str'>]
      name:
        string value required [code=modelity.UNSUPPORTED_VALUE_TYPE, value_type=<class 'bool'>]

When data did not pass parsing stage, then :exc:`modelity.exc.ParsingError`
exception is raised.

Failure at validation stage
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When parsing stage is completed successfully then each field has correct value.
But this does not imply that required fields were present or that the cross
field dependencies are valid. It is necessary to validate. And validation can
fail:

.. doctest::

    >>> from modelity.helpers import load
    >>> untrusted_valid_data = {
    ...     "surname": "Black",
    ...     "dob": "1999-01-31",
    ... }
    >>> person = load(Person, untrusted_valid_data)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'Person' failed with 1 error(-s):
      name:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]

In this case, :exc:`modelity.exc.ValidationError` exception is raised to signal
that each individual field is okay, but model as a whole thing is not.

Serializing models
------------------

Models can be converted back to the "wire" format that is as close to JSON as
possible. Modelity, however, does not convert models to JSON string directly
(there are separate tools for that), but to a :class:`dict` objects that
ideally should already be JSON-encodable.

To convert model to the dict, a :func:`modelity.helpers.dump` function must be
used:

.. doctest::

    >>> from modelity.helpers import dump
    >>> dump(full)
    {'name': 'Bridget', 'second_name': 'Rose', 'surname': 'Jones', 'dob': '1969-11-09'}

Serialization by default includes all fields in the output. However, there are
predefined options to skip certain fields, like unset ones:

.. doctest::

    >>> empty = Person()
    >>> dump(empty)
    {'name': Unset, 'second_name': Unset, 'surname': Unset, 'dob': Unset}
    >>> dump(empty, exclude_unset=True)
    {}

The function :func:`modelity.model.dump` is a thin wrapper around
:meth:`modelity.model.Model.dump` model's method, that contains more generic
interface. For more information please proceed to the API docs.
