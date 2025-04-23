Built-in types
==============

**typing.Any**
--------------

Use :obj:`typing.Any` annotation to declare fields that can be assigned with
any type:

.. testcode::

    import typing

    from modelity.model import Model

    class Dummy(Model):
        foo: typing.Any

.. doctest::

    >>> dummy = Dummy()
    >>> dummy.foo = 123
    >>> dummy.foo
    123
    >>> dummy.foo = "spam"
    >>> dummy.foo
    'spam'
    >>> dummy.foo = {}
    >>> dummy.foo
    {}

**bool**
--------

Use :class:`bool` type for fields that store boolean values:

.. testcode::

    from modelity.model import Model

    class DoorLock(Model):
        locked: bool

.. doctest::

    >>> lock = DoorLock()
    >>> lock.locked = True
    >>> lock.locked
    True
    >>> lock.locked = False
    >>> lock.locked
    False

By default, :class:`bool` only allows assignment to either ``True`` or
``False`` and will fail for other types:

.. doctest::

    >>> lock.locked = 'yes'
    Traceback (most recent call last):
        ...
    modelity.exc.ParsingError: parsing failed for type 'DoorLock' with 1 error(-s):
      locked:
        not a valid boolean value [code=modelity.INVALID_BOOL, value_type=<class 'str'>]

It is possible to configure :class:`bool` type with some predefined constants
that will evaluate to either ``True`` or ``False``. For example, it is possible
to declare field that will also accept ``"yes"`` string as ``True``, and
``"no"`` as ``False``:

.. testcode::

    from modelity.model import Model, FieldInfo

    class DoorLock(Model):
        locked: bool = FieldInfo(type_opts=dict(true_literals=['yes'], false_literals=['no']))

Now, in addition to normal :class:`bool` values, *locked* field can also be set
to ``"yes"`` or ``"no"``:

.. doctest::

    >>> lock = DoorLock()
    >>> lock.locked = 'yes'
    >>> lock.locked
    True
    >>> lock.locked = 'no'
    >>> lock.locked
    False

The literal, however, must exactly match input value to become a boolean. For
example, entering ``"YES"`` will fail, as ``"YES"`` is not present in the set
of true or false literals:

.. doctest::

    >>> lock.locked = 'YES'
    Traceback (most recent call last):
        ...
    modelity.exc.ParsingError: parsing failed for type 'DoorLock' with 1 error(-s):
      locked:
        not a valid boolean value [code=modelity.INVALID_BOOL, value_type=<class 'str'>]

.. _types-datetime.datetime:

**datetime.datetime**
---------------------

Modelity supports :class:`datetime.datetime` field type that can parse either
datetime object, or an ISO8601 string in several formats:

.. testcode::

    import datetime

    from modelity.model import Model

    class Entry(Model):
        created: datetime.datetime

.. doctest::

    >>> entry = Entry()
    >>> entry.created = datetime.datetime(2025, 4, 23, 10, 11, 12)
    >>> entry
    Entry(created=datetime.datetime(2025, 4, 23, 10, 11, 12))
    >>> entry.created = "2025-04-23T10:11:12"
    >>> entry.created
    datetime.datetime(2025, 4, 23, 10, 11, 12)

It is possible to set user-defined input formats (for parsing) and/or output
format (for serializing):

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

These settings override default ones, so now the parser will only parse string
as a valid datetime only if the string has one of the format configured above:

.. doctest::

    >>> entry = Entry()
    >>> entry.created = "2000-01-01T10:11:22"
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'Entry' with 1 error(-s):
      created:
        unsupported datetime format; supported formats: MM-DD-YYYY hh:mm:ss [code=modelity.UNSUPPORTED_DATETIME_FORMAT, value_type=<class 'str'>]

Only datetime string values matching format specified above will be parsed
successfully:

.. doctest::

    >>> entry.created = "12-24-2024 10:11:22"
    >>> entry.created
    datetime.datetime(2024, 12, 24, 10, 11, 22)

And when serializing model, *created* field will be formatted according to the
**output_datetime_format** set:

.. doctest::

    >>> from modelity.model import dump
    >>> dump(entry)
    {'created': '12-24-2024 10:11:22'}

The list of supported date/time components placeholders is following:

* ``YYYY`` - for a 4-digit year (f.e. 2024)
* ``MM`` - for a 2-digit month number (01 - 12)
* ``DD`` - for a 2-digit day number (01 - 31)
* ``hh`` - for a 2-digit hour (00 - 23)
* ``mm`` - for a 2-digit minute (00 - 59)
* ``ss`` - for a 2-digit second (00 - 59)
* ``ZZZZ`` - for a 5-digit timezone offset (f.e. +0200)

**datetime.date**
-----------------

Modelity also supports :class:`datetime.date` class as a field type, with
default ``YYYY-MM-DD`` input format:

.. testcode::

    import datetime

    from modelity.model import Model

    class Person(Model):
        dob: datetime.date

.. doctest::

    >>> person = Person()
    >>> person.dob = datetime.date(1990, 1, 31)
    >>> person.dob
    datetime.date(1990, 1, 31)
    >>> person.dob = "1990-01-31"
    >>> person.dob
    datetime.date(1990, 1, 31)

And, like for :ref:`types-datetime.datetime`, there also options for
configuring formatting available:

.. testcode::

    import datetime

    from modelity.model import Model, FieldInfo

    class Person(Model):
        dob: datetime.date =\
            FieldInfo(
                type_opts=dict(
                    input_date_formats=['MM-DD-YYYY'],
                    output_date_format='MM-DD-YYYY'
                )
            )

.. doctest::

    >>> person = Person()
    >>> person.dob = "1990-01-31"
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'Person' with 1 error(-s):
      dob:
        unsupported date format; supported formats: MM-DD-YYYY [code=modelity.UNSUPPORTED_DATE_FORMAT, value_type=<class 'str'>]
    >>> person.dob = "01-31-1990"
    >>> person.dob
    datetime.date(1990, 1, 31)

The list of supported date/time components placeholders is following:

* ``YYYY`` - for a 4-digit year (f.e. 2024)
* ``MM`` - for a 2-digit month number (01 - 12)
* ``DD`` - for a 2-digit day number (01 - 31)

Enumerated types
----------------

Modelity supports enumerated types created by inheriting from
:class:`enum.Enum` base class. For example:

.. testcode::

    import enum

    from modelity.model import Model

    class Transmission(enum.Enum):
        MANUAL = 'manual'
        AUTOMATIC = 'automatic'

    class Car(Model):
        transmission: Transmission

.. doctest::

    >>> car = Car()
    >>> car.transmission = 'manual'
    >>> car.transmission
    <Transmission.MANUAL: 'manual'>
    >>> car.transmission = Transmission.AUTOMATIC
    >>> car.transmission
    <Transmission.AUTOMATIC: 'automatic'>

When serializing enumerated type, then enum values are written to the output:

.. doctest::

    >>> from modelity.model import dump
    >>> dump(car)
    {'transmission': 'automatic'}

Literal types
-------------

Python has a :obj:`typing.Literal` type for specifying list of allowed
constants. This can be used to list the only valid values for a given field:

.. testcode::

    import typing

    from modelity.model import Model

    class Object(Model):
        version: typing.Literal['1.0']

.. doctest::

    >>> obj = Object()
    >>> obj.version = "1.0"
    >>> obj.version
    '1.0'

And similar to enums, raw values are written to the output when serializing
literal fields:

.. doctest::

    >>> from modelity.model import dump
    >>> dump(obj)
    {'version': '1.0'}
