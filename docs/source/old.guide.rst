.. _guide:

User's guide
============

Model classes
-------------

Required fields
^^^^^^^^^^^^^^^

By default, all fields declared for a model are **required** unless wrapped
with :obj:`typing.Optional` or :obj:`modelity.types.StrictOptional` type
wrappers:

.. testcode::

    from modelity.model import Model

    class User(Model):
        name: str  # this field is required
        email: str  # this field is required
        age: int  # this field is required

In Modelity, presence of required fields is checked at validation stage,
therefore it is fine to declare uninitialized model and fill it with data
later:

.. doctest::

    >>> from modelity.helpers import validate
    >>> bob = User()  # this WILL NOT fail in runtime (but static type checkers may argue)
    >>> validate(bob)  # this WILL fail; 3 required fields are missing: name, email and age
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'User' failed with 3 error(-s):
      age:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      email:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]
      name:
        this field is required [code=modelity.REQUIRED_MISSING, data={}]

Now, let's fill the missing required fields and call
:func:`modelity.helpers.validate` helper again. It will no longer fail:

.. doctest::

    >>> bob.name = 'Bob'
    >>> bob.email = 'bob@example.com'
    >>> bob.age = 24
    >>> validate(bob)  # All required fields are now set

.. _guide-optionalFields:

Optional fields
^^^^^^^^^^^^^^^

To mark field as optional, simply use :obj:`typing.Optional` type wrapper. For
example, let's add new optional *phone* field to our **User** model from
previous example:

.. testcode::

    from typing import Optional

    from modelity.model import Model
    from modelity.helpers import validate

    class User(Model):
        name: str
        email: str
        age: int
        phone: Optional[str]

Optional fields does not have to be set to pass validation:

.. doctest::

    >>> alice = User(name='Alice', email='alice@example.com', age=25)
    >>> validate(alice)  # The `alice` object is valid, as all required fields are set

But they still need to have valid type when set:

.. doctest::

    >>> alice.phone = 123456789  # must be string
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'User' with 1 error(-s):
      phone:
        string value required [code=modelity.UNSUPPORTED_VALUE_TYPE, value_type=<class 'int'>]

Optional fields can also be set to ``None``:

    >>> alice.phone = None
    >>> alice.phone is None
    True

.. important::

   In Modelity, setting optional field to ``None`` and not setting it at all
   are **two completely different things**. This unique feature can be used to
   differentiate the intention of clearing the field (when field is set to
   ``None``) from not touching it (when it is unset).

Strict optional fields
^^^^^^^^^^^^^^^^^^^^^^

Modelity allows to declare so called **strict optional** fields with the use of
:obj:`modelity.types.StrictOptional` type wrapper. Strict optionals, unlike
standard optionals, allow the field to either be set to instance of given type
**T** or not set at all, disallowing ``None``. For example, let's add
*middle_name* field and use strict optional for it:

.. testcode::

    from typing import Optional

    from modelity.model import Model
    from modelity.helpers import validate
    from modelity.types import StrictOptional

    class User(Model):
        name: str
        middle_name: StrictOptional[str]  # strict optional; string or unset
        email: str
        age: int
        phone: Optional[str]  # standard optional; string, None or unset

Now let's check how this works:

.. doctest::

    >>> jane = User(name='Jane', email='jane@example.com', age=32)
    >>> validate(jane)  # The object is valid; only optional fields are missing
    >>> jane.middle_name = 'Alice'  # OK
    >>> jane.middle_name = None  # fail; None is not allowed
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'User' with 1 error(-s):
      middle_name:
        could not parse union value; types tried: <class 'str'>, <class 'modelity.unset.UnsetType'> [code=modelity.UNION_PARSING_ERROR, value_type=<class 'NoneType'>]

Optional union fields
^^^^^^^^^^^^^^^^^^^^^

Union fields allow the field to be set to instance of one of specified types.
To make such fields optional, simply add ``None`` to the list of types, or
:class:`modelity.unset.UnsetType` type (for strict optionals). For example,
let's rewrite example from above and use unions instead:

.. testcode::

    from typing import Union

    from modelity.model import Model
    from modelity.helpers import validate
    from modelity.unset import UnsetType

    class User(Model):
        name: str
        middle_name: Union[str, UnsetType]  # strict optional; string or unset
        email: str
        age: int
        phone: Union[str, None]  # standard optional; string, None or unset

The example from above will behave exactly the same:

.. doctest::

    >>> jane = User(name='Jane', email='jane@example.com', age=32)
    >>> validate(jane)  # The object is valid; only optional fields are missing
    >>> jane.middle_name = 'Alice'  # OK
    >>> jane.middle_name = None  # fail; None is not allowed
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'User' with 1 error(-s):
      middle_name:
        could not parse union value; types tried: <class 'str'>, <class 'modelity.unset.UnsetType'> [code=modelity.UNION_PARSING_ERROR, value_type=<class 'NoneType'>]

Attaching metadata to fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each field in a model can have additional metadata attached. This is used to
set default values, default value factory functions, customizing type parsers
and more. For example, let's define default value factory for a field. To do
this, we need :func:`modelity.model.field_info` helper function:

.. testcode::

    from modelity.model import Model, field_info

Default values
^^^^^^^^^^^^^^

The simplest way to define a default value for a field is to initialize it with
the default value:

.. testcode::

    from modelity.model import Model
    from modelity.helpers import validate

    class DefaultExample(Model):
        foo: int = 1
        bar: str = 'spam'

When field has default value set, that default value will be used to initialize
the field when model is initialized and there are no explicit values given for
that fields:

.. doctest::

    >>> one = DefaultExample()
    >>> validate(one)  # this will be valid; all required fields have default values defined
    >>> one
    DefaultExample(foo=1, bar='spam')

Default values can be shadowed if another value is given explicitly for a
field:

.. doctest::

    >>> two = DefaultExample(foo=123)
    >>> two.foo  # no longer default
    123
    >>> two.bar  # still default
    'spam'

Default values are normally parsed when model is constructed, so incorrect
default value will cause error during model object construction:

.. testcode::

    class InvalidDefaultExample(Model):
        foo: int = 'not an integer'

.. doctest::

    >>> obj = InvalidDefaultExample()
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: parsing failed for type 'InvalidDefaultExample' with 1 error(-s):
      foo:
        could not parse value as integer number [code=modelity.PARSING_ERROR, value_type=<class 'str'>]

This happens because for Modelity default values are no different from the
values given by the user. However, if the value is explicitly given for a field
with incorrect default and a valid value is given, then there will be no error
at all:

.. doctest::

    >>> obj = InvalidDefaultExample(foo=123)
    >>> obj.foo
    123

Using default value factories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes it is needed to calculate default value instead of using fixed one.
For example, we need our model to have ID property that must be unique for each
created instance, like in this example:

.. testcode::

    import itertools

    from modelity.model import Model, field_info

    _id_gen = itertools.count(1)

    class User(Model):
        id: int = field_info(default_factory=lambda: next(_id_gen))
        name: str

Now let's see this in action:

.. doctest::

    >>> john = User(name='John')
    >>> alice = User(name='Alice')
    >>> alice.id > john.id
    True

When default factory is used, same principles apply as for normal default
values.

Default mutable values
^^^^^^^^^^^^^^^^^^^^^^

Models can safely be declared with mutable default values, like dicts or lists:

.. testcode::

    from modelity.model import Model

    class MutableDefaultExample(Model):
        foo: dict = {}

Modelity checks if given default value is mutable and, if so, deep copies it to
the newly created model object instead of just passing it as is:

.. doctest::

    >>> obj = MutableDefaultExample()
    >>> obj.foo
    {}
    >>> obj.foo is not MutableDefaultExample.__model_fields__['foo'].field_info.default
    True

Using constraints
^^^^^^^^^^^^^^^^^

.. _guide-workingWithModelObjects:

Working with model objects
--------------------------

Creating model instances
^^^^^^^^^^^^^^^^^^^^^^^^

Updating model instances
^^^^^^^^^^^^^^^^^^^^^^^^

Checking if field is set
^^^^^^^^^^^^^^^^^^^^^^^^

Unsetting fields
^^^^^^^^^^^^^^^^

Validating models
^^^^^^^^^^^^^^^^^

Serializing models
^^^^^^^^^^^^^^^^^^

Deserializing models from unsafe data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Data processing stages
----------------------

Introduction
^^^^^^^^^^^^

Data parsing pipeline
^^^^^^^^^^^^^^^^^^^^^

Using preprocessors
~~~~~~~~~~~~~~~~~~~

Using postprocessors
~~~~~~~~~~~~~~~~~~~~

Model validation
^^^^^^^^^^^^^^^^

Using model prevalidators
~~~~~~~~~~~~~~~~~~~~~~~~~

Using field validators
~~~~~~~~~~~~~~~~~~~~~~

Using model postvalidators
~~~~~~~~~~~~~~~~~~~~~~~~~~

Built-in types
--------------

Registering custom types
------------------------

By declaring ``__modelity_type_descriptor__`` static method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By using ``type_descriptor_factory`` decorator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Advanced validation patterns
----------------------------

tbd
