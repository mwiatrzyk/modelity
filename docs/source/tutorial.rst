Tutorial
========

Creating data model classes
---------------------------

To create data model class in Modelity you have to inherit from
:class:`modelity.model.Model` base class and declare fields using type
annotations. For example, let's create a class **Person** having three required
fields: name, surname and date of birth:

.. testcode::

    from datetime import date

    from modelity.model import Model

    class Person(Model):
        name: str
        surname: str
        dob: date

Creating data model instances
-----------------------------

Now the model can be instantiated into Python object just like a typical Python
class. However, unlike dataclasses, Modelity only allows keyword arguments and
does not force required fields to be initialized during object construction.
Therefore, all following declarations are correct:

.. testcode::

    first = Person()
    second = Person(name="John", surname="Doe", dob=date(1980, 1, 1))
    third = Person(name="Jane", surname="Doe")

Although this may seem odd, in Modelity defacto all fields are implicitly
optional in terms of initialization, and any lack of required fields is
detected later, at the validation stage.

The models can also be initialized from external data, like JSON file, API
response etc. The only requirement is to parse incoming data into the dict, and
later pass to the model like this:

.. testcode::

    data = {
        "name": "Jack",
        "surname": "Black",
        "dob": "2000-01-31"
    }

    jack_black = Person(**data)

No matter which way of model initialization is chosen, underneath the same data
parsing code is executed, and given data is parsed to the type that was
specified in the model declaration:

.. doctest::

    >>> jack_black.dob
    datetime.date(2000, 1, 31)

Modelity also ignores any extra arguments passed to the constructor, like in
this example:

.. doctest::

    >>> Person(dummy="spam")
    Person(name=Unset, surname=Unset, dob=Unset)

The model **Person** contains no field named *dummy*, so the additional
argument was ignored. This allows Modelity to extract viable data from the
given input, and ignore fields it is not interested in.

Data processing stages
----------------------

Data parsing stage
^^^^^^^^^^^^^^^^^^

Data parsing stage is first stage of data processing that takes place when
model is instantiated or modified.

During data parsing, each initialized field is checked for type correctness,
and parsing attempt is performed if there is type mismatch detected. Finally,
all fields that were set have correct type.

Check the example below:

.. testcode::

    class Dummy(Model):
        foo: int

We have created model named **Dummy**, with single integer field named *foo*.
When this field is initialized with integer value, then the value is simply
assigned and nothing really happens:

.. doctest::

    >>> Dummy(foo=123)
    Dummy(foo=123)

Now, let's set the same field with numeric string value. The value is not
integer, but it can be parsed as integer, and Modelity does this:

.. doctest::

    >>> Dummy(foo="123")
    Dummy(foo=123)

Same thing will happen if attribute is set later, when the model is
already instantiated:

.. doctest::

    >>> dummy = Dummy()
    >>> dummy.foo = 123
    >>> dummy.foo
    123
    >>> dummy.foo = "456"
    >>> dummy.foo
    456

On the other hand, if the type cannot be parsed, Modelity will fail with
:exc:`modelity.exc.ParsingError`:

.. doctest::

    >>> Dummy(foo="not an int")
    Traceback (most recent call last):
        ...
    modelity.exc.ParsingError: parsing failed for type 'Dummy' with 1 error(-s):
      foo:
        not a valid integer number [code=modelity.INVALID_NUMBER, value_type=<class 'str'>]

Data parsing stage is responsible for parsing the data and at this stage there
is not possible to check any cross-field dependencies, as Modelity does not
know in what order will the fields be initialized. To fix this gap, Modelity
provides second, separated stage of data processing - data validation.

Data validation stage
^^^^^^^^^^^^^^^^^^^^^

Unlike other similar tools, Modelity does not run validation on its own and
completely depends on the user. Thanks to this, validation can be executed and
any time, when it is already known that parsing stage has already been
finished. To run validation, you need to import and call
:func:`modelity.model.validate` function on the model you need to validate.

Let's go back to the **Person** class from the previous section. That class
have 3 required fields, so let's check if the empty instance is valid:

.. testcode::

    from modelity.model import validate

    person = Person()
    validate(person)

Of course, empty **Person** object is not valid, as it must have all 3 required
fields set:

.. testoutput::

    Traceback (most recent call last):
        ...
    modelity.exc.ValidationError: validation of model 'Person' failed with 3 error(-s):
      dob:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      name:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      surname:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]

To differentiate validation stage errors from parsing stage errors, Modelity
provides separate :exc:`modelity.exc.ValidationError` exception class that was
raised in the example above.

The model API
-------------

Now let's have quick overview of the model API. For the purpose of this
example, let's create instance of **Person** class again:

.. doctest::

    >>> person = Person(name="John", surname="Doe")
    >>> person
    Person(name='John', surname='Doe', dob=Unset)

Comparing models
^^^^^^^^^^^^^^^^

Two models can be compared:

.. doctest::

    >>> person == Person()
    False
    >>> person == Person(name="John", surname="Doe")
    True

Two models can only be equal if both are instances of same model class. Two
instances of two different model classes can never be equal, even if fields are
the same:

.. testcode::

    class One(Model):
        foo: int

    class Two(Model):
        foo: int

.. doctest::

    >>> One() == Two()
    False
