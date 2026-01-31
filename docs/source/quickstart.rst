.. _quickstart:

Quickstart
==========

This guide walks you through the basic usage of Modelity - from installing the
library to parsing, validating and serializing structured data.

Installation
------------

Modelity is available on PyPI and can be installed or added to your
project's dependencies using any available Python package manager.

For example, to install Modelity using **pip**, run following command::

    $ pip install modelity

Defining a model class
----------------------

Once Modelity is installed, the next step is to define data models. To do so,
just extend :class:`modelity.model.Model` class and provide fields using type
annotations:

.. testcode::

    from modelity.model import Model

    class User(Model):
        name: str
        email: str
        age: int

Creating model instances
------------------------

To create an instance of defined model class, provide field names and values
using keyword arguments:

.. doctest::

    >>> alice = User(name='Alice', email='alice@example.com', age='25')  # age is parsed from str to int
    >>> alice.name
    'Alice'
    >>> alice.email
    'alice@example.com'
    >>> alice.age
    25

Modelity automatically checks if values have the right type and tries to
perform necessary conversions whenever needed. If the type of the input value
is not correct and Modelity failed trying to parse it, then
:exc:`modelity.exc.ParsingError` will be raised:

.. doctest::

    >>> bob = User(name='Bob', email='bob@example.com', age='30 yrs')  # age is not valid, as it is not a numeric value
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'User':
      age:
        Not a valid int value [code=modelity.PARSE_ERROR, value_type=str, expected_type=int]

Modelity does not force you to give all the required arguments during
construction, as presence of required fields is checked during validation
stage. This allows creating empty model instances and filling them with data
later, for example using interactive prompts:

.. testcode::
    :hide:

    def prompt_name(msg):
        return 'Joe'

    def prompt_email(msg):
        return 'joe@example.com'

.. doctest::

    >>> joe = User()  # This is perfectly valid in Modelity (although some static code checkers may argue)
    >>> joe.name = prompt_name('What is your name?')  # answer: Joe
    >>> joe.email = prompt_email('What is your e-mail address?')  # answer: joe@example.com
    >>> joe.name
    'Joe'
    >>> joe.email
    'joe@example.com'

Validating model instances
--------------------------

Modelity clearly differentiates between data parsing (happening when models are
created or modified) and data validation stages. The latter is explicit and
needs to be manually triggered by the user when model initialization or
modification is already done. The need to validate explicitly is one of core
Modelity features - it allows to fill the model with data step-by-step and
validate when the model is ready. Thanks to this, validators can assume that
the model is complete and contains values of right types. This makes validation
simpler.

To validate model instance, use :func:`modelity.helpers.validate` helper
function:

.. doctest::

    >>> from modelity.helpers import validate
    >>> validate(alice)

If the model is valid, the function will not raise any exceptions. Otherwise,
:exc:`modelity.exc.ValidationError` will be raised. For example, ``joe``
(created earlier) has required *age* property missing:

.. doctest::

    >>> validate(joe)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'User':
      age:
        This field is required [code=modelity.REQUIRED_MISSING]


Serializing model instances
---------------------------

Serialize models to :class:`dict` object using :func:`modelity.helpers.dump` helper function:

.. doctest::

    >>> from modelity.helpers import dump
    >>> alice_dict = dump(alice)
    >>> alice_dict
    {'name': 'Alice', 'email': 'alice@example.com', 'age': 25}

Now, resulting dict can be encoded, for example, to JSON using
:func:`json.dumps` function from Python's standard library:

.. doctest::

    >>> import json
    >>> json.dumps(alice_dict)
    '{"name": "Alice", "email": "alice@example.com", "age": 25}'

.. important::

    The :func:`modelity.helpers.dump` helper does not validate the model
    automatically.

Deserializing data into model instances
---------------------------------------

For deserialization, use :func:`modelity.helpers.load` helper function:

.. doctest::

    >>> from modelity.helpers import load
    >>> load(User, alice_dict)
    User(name='Alice', email='alice@example.com', age=25)

Alternatively, :func:`modelity.helpers.ModelLoader` helper function can be used
to achieve same thing, but with a class-like feeling:

.. doctest::

    >>> from modelity.helpers import ModelLoader
    >>> UserLoader = ModelLoader(User)
    >>> UserLoader(**alice_dict)
    User(name='Alice', email='alice@example.com', age=25)

During deserialization, both stages (parsing + validation) are executed
automatically, so the deserialized data have to be valid, or otherwise
:exc:`modelity.exc.ParsingError` or :exc:`modelity.exc.ValidationError`
exception will be raised, depending on whether it failed during parsing, or
validation:

.. doctest::

    >>> UserLoader(age="25 yrs")
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'User':
      age:
        Not a valid int value [code=modelity.PARSE_ERROR, value_type=str, expected_type=int]

.. doctest::

    >>> UserLoader(name="Mike")
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 2 validation errors for model 'User':
      age:
        This field is required [code=modelity.REQUIRED_MISSING]
      email:
        This field is required [code=modelity.REQUIRED_MISSING]
