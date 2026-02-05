.. _guide:

User's guide
============

Core principles
---------------

Models are defined using type annotations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity uses type annotations to declare fields, just like via
:func:`dataclasses.dataclass` decorator. The only difference is the need of
use :class:`modelity.model.Model` as a base class:

.. testcode::

    from modelity.model import Model

    class User(Model):
        name: str
        email: str
        age: int

Use of ``__slots__`` instead of descriptors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All models created using Modelity are implicitly using
:class:`modelity.model.ModelMeta` as metaclass. This metaclass provides
inheritance handling and generation of the ``__slots__`` attribute in models.
Modelity does not override field reading in any way, there is Python's built-in
logic used underneath when fields are read. Instead, Modelity overrides
``__setattr__`` and injects data parsing logic there. As a result, model read
operations are fast.

Built-in ``Unset`` constant for unset fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity uses special built-in :class:`modelity.unset.UnsetType` singleton
class with provided built-in :obj:`modelity.unset.Unset` object to
represent the unset state of model fields. When model object is created,
all fields are initially set to ``Unset``, unless user-defined value is
provided:

.. testcode::

    from modelity.api import Model, Unset

    class User(Model):
        name: str
        email: str
        age: int

.. doctest::

    >>> user = User(age=27)  # 'name' and 'email' are unset
    >>> user.name is Unset  # check if 'name' is unset
    True
    >>> user.email is Unset  # check if 'email' is unset
    True
    >>> user.age
    27

Thanks to this special sentinel, fields that are unset are different from
fields that are set to ``None``. Moreover, with this feature ``None``
becomes a **first-class value** and must be explicitly accepted as a field's
valid value.

Mutability of models is important
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity aims to provide full support for mutable types to prevent from
breaking model constraints when model is modified. For example, modifying *age*
invokes same parsing logic as used during model construction:

.. doctest::

    >>> bob = User(name='Bob', email='bob@example.com', age='27')  # age will be converted to integer
    >>> bob.age
    27
    >>> bob.age = 'not an int'  # modifying with invalid type will fail
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'User':
      age:
        Not a valid int value [code=modelity.PARSE_ERROR, value_type=str, expected_type=int]
    >>> bob.age = '26'  # this will automatically be converted to integer
    >>> bob.age
    26

Same logic is used for fields being declared as typed mutable containers.
For example, let's create a list of users:

.. testcode::

    from modelity.model import Model

    class UserStorage(Model):
        users: list[User]

.. doctest::

    >>> storage = UserStorage(users=[])  # initialize with empty list
    >>> storage.users.append(bob)  # append 'bob'
    >>> storage.users.append({
    ...     'name': 'Alice',
    ...     'email': 'alice@example.com',
    ...     'age': '25'
    ... })  # will be converted to User
    >>> storage.users[0]
    User(name='Bob', email='bob@example.com', age=26)
    >>> storage.users[1]
    User(name='Alice', email='alice@example.com', age=25)
    >>> storage.users.append(123)  # not allowed; cannot be converted to User
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'list[User]':
      2:
        Not a valid value; expected: User [code=modelity.INVALID_TYPE, value_type=int, expected_types=[User], allowed_types=[Mapping]]

.. note::

    Current version of Modelity has built-in support for following mutable
    types:

    * **list[T]**
    * **set[T]**
    * **dict[K, V]**

Input data parsing is separated from model validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity splits data processing into two stages: **parsing**, where models are
constructed from raw data, and **validation**, where integrity of existing
model instance is checked.

Input data parsing is executed automatically whenever model object is created,
field in an existing model is set, or when field of mutable type is modified.
The role of this stage is to ensure that input value has the right type at the
end of assignment or modification. Data parsing is executed for each field in
separation. If the type of the input value is incorrect and conversion was not
successful, then :exc:`modelity.exc.ParsingError` exception is raised at this
stage.

Model validation, unlike input data parsing, happens on user's demand and is
performed with :func:`modelity.helpers.validate` helper. The role of this stage
is to ensure presence of required fields and to ensure that any user-defined
cross-field dependencies are met. Model validation happens on per-model basis,
therefore validators have access to entire model. Validators also do not have
to check field types, as this was already performed by input data parsing
stage. The ability to run validation on demand allows the user to progressively
fill the model with data and validate once the model initialization is done.
Failure of validation is signalled using :exc:`modelity.exc.ValidationError`
exception.

Presence of required fields is checked at validation stage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Although this may be pointed out as error by static code analyzers,
Modelity does not force you to initialize your model classes with all
required fields set. You can, of course, but this is not required. Thanks
to this, it is possible to initialize models progressively, as user of
your app enters the data, with no need of filling required fields with fake
data:

.. doctest::

    >>> from modelity.helpers import validate
    >>> user = User()  # OK for Modelity, but linters may point this as error
    >>> user.name = 'John'
    >>> user.email = 'john@example.com'
    >>> validate(user)  # failure; required 'age' is missing
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'User':
      age:
        This field is required [code=modelity.REQUIRED_MISSING]
    >>> user.age = 32  # Fill the missing data
    >>> validate(user)  # OK

Defining a model class
----------------------

Introduction
^^^^^^^^^^^^

To create your own data models using Modelity you have to inherit from
:class:`modelity.model.Model` base class and provide zero or more fields using
type annotations.

Here is the simplest possible model that can be declared using Modelity:

.. testcode::

    from modelity.model import Model

    class Simplest(Model):
        pass

That model has no fields and basically has no practical use. But it can be used
as a base class for other models, allowing to later add field- or model-level
hooks that will automatically be used by subclasses. There will be more on this
topic in advanced guide.

To create model with fields, just add one or more using type annotations:

.. testcode::

    from modelity.model import Model

    class SingleField(Model):
        foo: int  # field named 'foo' of type 'int'

When fields are defined, Modelity performs a lookup of built-in so called
**type descriptor** and attaches it to the field when model type is created.
The type descriptor provides type-specific parsing and visitation logic and can
use other type descriptors internally for complex types. Type descriptor lookup
is performed only once and only when new type is created. If no type descriptor
could be found, then following error is reported:

.. doctest::

    >>> from modelity.model import Model
    >>> class WrongType(Model):
    ...     foo: object
    Traceback (most recent call last):
      ...
    modelity.exc.UnsupportedTypeError: unsupported type used: <class 'object'>

.. _guide-optional:

Optional fields
^^^^^^^^^^^^^^^

Optional fields can be declared using any of the methods depicted below.

.. _guide-optional-optional:

Using ``typing.Optional[T]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Values allowed:

* instances of type **T**
* instances of type **U** that can be parsed into **T**
* ``None`` value

.. important::

   Since version 0.29.0 optional fields do not allow ``Unset`` as a valid
   value and all unset ``Optional[T]`` fields will be rejected during model
   validation phase.

   This is due to the fact that ``Optional[T]`` is basically ``Union[T,
   NoneType]`` and ``Unset`` simply does not fit. Thanks to this additional
   check you can safely write e.g.::

        model = load_model_from_somewhere()  # `model.foo` can either be T, None or Unset
        ...
        validate(model)  # Validate model; will fail if `model.foo` is unset
        if model.foo is not None:  # Now `model.foo` will either be T, or None 
            return model.foo  # Not None, so it will be T

   The best way to avoid leaving optional fields unset is to declare such
   fields with ``None`` as default value::

        class Dummy(Model):
            foo: Optional[int] = None

   See also:
   
   * :obj:`modelity.types.LooseOptional`

Example:

.. testcode::

    from typing import Optional

    from modelity.model import Model
    from modelity.helpers import validate

    class OptionalExample(Model):
        foo: Optional[int] = None

.. doctest::

    >>> obj = OptionalExample()
    >>> validate(obj)  # OK; all fields are optional
    >>> obj.foo = 123  # OK; valid integer
    >>> obj.foo = '456'  # OK; can be converted to integer
    >>> obj.foo
    456
    >>> obj.foo = None  # OK; None is allowed
    >>> obj.foo is None
    True

.. _guide-optional-strictOptional:

Using ``modelity.types.StrictOptional[T]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Values allowed:

* instances of type **T**
* instances of type **U** that can be parsed as or converted into **T**

Example:

.. testcode::

    from modelity.model import Model
    from modelity.helpers import validate
    from modelity.types import StrictOptional

    class StrictOptionalExample(Model):
        foo: StrictOptional[int]

.. doctest::

    >>> obj = StrictOptionalExample()
    >>> validate(obj)  # OK
    >>> obj.foo = 123  # OK; valid integer
    >>> obj.foo = '456'  # OK; can be converted to integer
    >>> obj.foo
    456
    >>> obj.foo = None  # fail; None is not allowed for strict optionals
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'StrictOptionalExample':
      foo:
        This field does not allow None; expected: Union[int, UnsetType] [code=modelity.NONE_NOT_ALLOWED, value_type=NoneType, expected_type=Union[int, UnsetType]]

.. important::

    Strict optionals do not allow ``None``; the field can only be set to valid
    instance of type **T** or not set at all.

Using ``modelity.types.LooseOptional[T]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 0.28.0

Values allowed:

* instances of type **T**
* instances of type **U** that can be parsed as or converted into **T**
* ``None`` value
* ``Unset`` value

Example:

.. testcode::

    from modelity.api import Model, validate, LooseOptional

    class LooseOptionalExample(Model):
        foo: LooseOptional[int]

.. doctest::

    >>> obj = LooseOptionalExample()
    >>> validate(obj)  # OK
    >>> obj.foo = 123  # OK; valid integer
    >>> obj.foo = '456'  # OK; can be converted to integer
    >>> obj.foo
    456
    >>> obj.foo = None  # OK
    >>> obj.foo is None
    True
    >>> obj.foo = Unset  # OK
    >>> obj.foo
    Unset

Using ``typing.Union[T, U, ..., None]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Values allowed:

* instances of type **T**
* instances of type **U**
* ...
* ``None`` value

Example:

.. testcode::

    from typing import Union

    from modelity.model import Model
    from modelity.helpers import validate

    class OptionalUnionExample(Model):
        foo: Union[int, str, None] = None

.. doctest::

    >>> obj = OptionalUnionExample()
    >>> validate(obj)  # OK
    >>> obj.foo = 123  # OK; valid integer
    >>> obj.foo = 'spam'  # OK; valid string
    >>> obj.foo = None  # OK

Using ``typing.Union[T, U, ..., UnsetType]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Values allowed:

* instances of type **T**
* instances of type **U**
* ...
* ``Unset`` value

Example:

.. testcode::

    from typing import Union

    from modelity.model import Model
    from modelity.types import UnsetType
    from modelity.helpers import validate

    class StrictOptionalUnionExample(Model):
        foo: Union[int, str, UnsetType]

.. doctest::

    >>> obj = StrictOptionalUnionExample()
    >>> validate(obj)  # OK
    >>> obj.foo = 123  # OK; valid integer
    >>> obj.foo = 'spam'  # OK; valid string
    >>> obj.foo = None  # fail; None is not allowed
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'StrictOptionalUnionExample':
      foo:
        Not a valid value; expected one of: int, str, UnsetType [code=modelity.INVALID_TYPE, value_type=NoneType, expected_types=[int, str, UnsetType]]

Using ``typing.Union[T, U, ..., NoneType, UnsetType]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Values allowed:

* instances of type **T**
* instances of type **U**
* ...
* ``None`` value
* ``Unset`` value

Example:

.. testcode::

    from typing import Union

    from modelity.model import Model
    from modelity.types import UnsetType
    from modelity.helpers import validate

    class StrictOptionalUnionExample(Model):
        foo: Union[int, str, None, UnsetType]

.. doctest::

    >>> obj = StrictOptionalUnionExample()
    >>> validate(obj)  # OK
    >>> obj.foo = 123  # OK; valid integer
    >>> obj.foo = 'spam'  # OK; valid string
    >>> obj.foo = None  # OK
    >>> obj.foo = Unset  # OK

Required fields
^^^^^^^^^^^^^^^

All fields that are not :ref:`optional<guide-optional>` are considered
**required**. For example:

.. testcode::

    import datetime

    from modelity.model import Model

    class User(Model):
        name: str  # required of type string
        email: str  # required of type string
        dob: datetime.date  # required of type datetime.date

However, unlike other data modelling tools, Modelity does not force presence of
required fields during initialization:

.. doctest::

    >>> user = User()  # this is allowed in runtime

This is one of the core Modelity features, allowing models to be progressively
filled in with data. To check if all required fields are present,
:func:`modelity.helpers.validate` helper must be used:

.. doctest::

    >>> from modelity.helpers import validate
    >>> validate(user)  # will fail, as all required fields are empty
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 3 validation errors for model 'User':
      dob:
        This field is required [code=modelity.REQUIRED_MISSING]
      email:
        This field is required [code=modelity.REQUIRED_MISSING]
      name:
        This field is required [code=modelity.REQUIRED_MISSING]

Now let's initialize required fields and validate again. Validation will no
longer fail:

.. doctest::

    >>> user.name = 'Joe'
    >>> user.email = 'joe@example.com'
    >>> user.dob = '1999-01-01'
    >>> validate(user)  # OK; all required fields are present

.. note::

    In Modelity, validation is completely up to the user and the specific use
    case. Modelity neither requires validation nor checks whether it has been
    performed.

Attaching metadata to fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity provides :class:`modelity.model.FieldInfo` class and a
:func:`modelity.model.field_info` factory function for attaching metadata to
model fields. It is recommended to use the latter, as it is better suited for
static code checking tools. Here's an example use:

.. testcode::

    import datetime

    from typing import Optional

    from modelity.model import Model, field_info
    from modelity.types import StrictOptional

    class User(Model):
        name: str = field_info(title='Name of the user', examples=['Joe', 'Bob', 'Alice'])  # field info used here
        email: str
        dob: datetime.date

In the example above, we've attached *title* and *examples* metadata parameters
to the *name* field. To access these metadata, use *__model_fields__* property
of the model class:

.. doctest::

    >>> User.__model_fields__['name'].field_info.title
    'Name of the user'

Accessing declared fields
^^^^^^^^^^^^^^^^^^^^^^^^^

Fields declared for a model can be accessed via
:attr:`modelity.model.ModelMeta.__model_fields__` attribute that is only
available for model type, not model instance. For example, we can list fields
that are available in the **User** model:

.. testcode::

    from modelity.model import Model

    class User(Model):
        name: str
        email: str
        age: int

.. doctest::

    >>> list(User.__model_fields__)
    ['name', 'email', 'age']

When accessing particular field, :class:`modelity.model.Field` object is
returned that can be used to access things like field name, field type, field
info etc.

.. doctest::

    >>> from modelity.model import Field
    >>> field = User.__model_fields__['name']
    >>> isinstance(field, Field)
    True
    >>> field.name
    'name'
    >>> field.typ
    <class 'str'>
    >>> field.is_optional()
    False

Setting default values
^^^^^^^^^^^^^^^^^^^^^^

When field has default value set, it implicitly becomes optional, even if it is
required. Default values are used when model object is created and no other
value was given for a field. Default values can be specified using any of the
methods given below.

Using direct assignment
~~~~~~~~~~~~~~~~~~~~~~~

.. testcode::

    from modelity.model import Model
    from modelity.helpers import validate

    class DirectAssignmentDefault(Model):
        foo: int = 123  # field of type int, with default value of 123

.. doctest::

    >>> obj = DirectAssignmentDefault()
    >>> validate(obj)  # OK; default value is used
    >>> obj.foo
    123

.. note::

    When direct assignment is used, default value is converted into
    :class:`modelity.model.FieldInfo` object implicitly and can be accessed like in this
    example:

    .. doctest::

        >>> DirectAssignmentDefault.__model_fields__['foo'].field_info.default
        123

Using ``modelity.model.field_info`` helper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is explicit form of direct assignment, allowing to set additional metadata
along with the default value. You just need to use
:func:`modelity.model.field_info` helper. For example:

.. testcode::

    from typing import Optional

    from modelity.model import Model, field_info
    from modelity.helpers import validate

    class User(Model):
        # Set both 'default' and 'title' for field
        middle_name: Optional[str] = field_info(default='', title="User's middle name")

.. doctest::

    >>> User.__model_fields__['middle_name'].field_info.title
    "User's middle name"
    >>> joe = User()
    >>> joe.middle_name
    ''

Using default factory
~~~~~~~~~~~~~~~~~~~~~

It is also possible to use :func:`modelity.model.field_info` helper to set
default value factory function instead of fixed default value. This is needed
for auto-generated IDs, unique keys, current dates, random values etc. For
example, we can use it to automatically assigned user ID:

.. testcode::

    import itertools

    from modelity.model import Model, field_info

    _id = itertools.count(1)

    class User(Model):
        id: int = field_info(default_factory=lambda: next(_id))

.. doctest::

    >>> one = User()
    >>> one.id
    1
    >>> two = User()
    >>> two.id
    2

Invalid default values
~~~~~~~~~~~~~~~~~~~~~~

In Modelity, default values are processed like any other values, so model
construction will fail if default value is incorrect and no other value was
given:

.. testcode::

    from modelity.model import Model

    class InvalidDefaultExample(Model):
        foo: int = 'not an int'

.. doctest::

    >>> InvalidDefaultExample() # fail; default value is not an integer
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'InvalidDefaultExample':
      foo:
        Not a valid int value [code=modelity.PARSE_ERROR, value_type=str, expected_type=int]
    >>> obj = InvalidDefaultExample(foo=123)  # OK; 123 shadows invalid default value
    >>> obj.foo
    123

.. important::

    You have to use the right type for default values to avoid unexpected
    parsing errors like the one from example above. This applies to all methods
    of default value declaration.

Annotating fields with constraints
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity provides support for :obj:`typing.Annotated` type wrapper allowing to
specify per-field constraints that can be found in :mod:`modelity.constraints`
module. For example, it is possible to restrict *email* field with a regular
expression that can only be satisfied by a valid e-mail address:

.. testcode::

    from typing import Annotated

    from modelity.model import Model
    from modelity.constraints import Regex

    class User(Model):
        email: Annotated[str, Regex(r'[a-z]+\@[a-z]+\.[a-z]{2,3}')]

Constraints are used to execute field-specific validation that is executed when
model object is created:

.. doctest::

    >>> bob = User(email='bob@example.com')  # OK
    >>> bob.email
    'bob@example.com'
    >>> alice = User(email='alice@example')  # wrong e-mail address
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'User':
      email:
        String does not match the expected format [code=modelity.INVALID_STRING_FORMAT, value_type=str, expected_pattern='[a-z]+\\@[a-z]+\\.[a-z]{2,3}']

Or when model object is modified:

.. doctest::

    >>> bob.email
    'bob@example.com'
    >>> bob.email = 'bob'
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'User':
      email:
        String does not match the expected format [code=modelity.INVALID_STRING_FORMAT, value_type=str, expected_pattern='[a-z]+\\@[a-z]+\\.[a-z]{2,3}']

Constraints are also verified during validation. Consider this example:

.. testcode::

    from typing import Annotated

    from modelity.model import Model
    from modelity.helpers import validate
    from modelity.constraints import MinLen, MaxLen

    class MutableListExample(Model):
        foo: Annotated[list, MinLen(1), MaxLen(4)]  # Mutable list with 1..4 elements

Field *foo* from the example above can be mutated after creation of the model.
This can potentially break constraints:

.. doctest::

    >>> obj = MutableListExample()  # OK; nothing is set
    >>> obj.foo = [1, 2, 3, 4]  # OK; 4 elements in the list
    >>> obj.foo.append(5)  # 5th element added, constraint is broken, but no error is reported

And now the validation will fail, as the constraints are no longer satisfied:

.. doctest::

    >>> obj.foo
    [1, 2, 3, 4, 5]
    >>> validate(obj)  # fail; too many elements
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'MutableListExample':
      foo:
        Expected length <= 4 [code=modelity.INVALID_LENGTH, max_length=4]

This is possible thanks to the one of the core features of Modelity library;
splitting data processing into data parsing and model validation.

.. note::

    You can create your own constraints by inheriting from
    :class:`modelity.interface.IConstraint` abstract base class.

Working with model objects
--------------------------

All examples in this section are based on this model type:

.. testcode::

    from modelity.model import Model

    class User(Model):
        name: str
        email: str
        age: int

Setting and unsetting fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Instantiating a model without arguments automatically sets all fields to
:obj:`modelity.unset.Unset` object:

.. doctest::

    >>> user = User()
    >>> user.name is Unset
    True
    >>> user.email is Unset
    True
    >>> user.age is Unset
    True

To set the field, you just need to assign it with a value of valid type:

.. doctest::

    >>> user.age = 27
    >>> user.age is Unset  # Now the `age` is not longer unset
    False
    >>> user.age
    27

If the field is tried to be set to a value of invalid type, then
:exc:`modelity.exc.ParsingError` is raised and the old value remains intact:

.. doctest::

    >>> user.age = 'not an int'
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'User':
      age:
        Not a valid int value [code=modelity.PARSE_ERROR, value_type=str, expected_type=int]
    >>> user.age
    27

After field is set, it can be unset. This can be achieved either by setting the
field with :obj:`modelity.unset.Unset` value, or by deleting model's attribute
that needs to be cleared. Both ways are equivalent:

.. doctest::

    >>> user.age = Unset
    >>> user.age is Unset
    True
    >>> user.age = 27
    >>> user.age
    27
    >>> del user.age
    >>> user.age
    Unset

Using ``repr`` on model objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Mockify supplies user-defined model with built-in implementation of the
``__repr__`` method that is used by :func:`repr` function. It can be used to
get string representation of the current model state. For example:

.. doctest::

    >>> user = User()
    >>> repr(user)
    'User(name=Unset, email=Unset, age=Unset)'
    >>> user.name = 'Bob'
    >>> user.email = 'bob@example.com'
    >>> repr(user)
    "User(name='Bob', email='bob@example.com', age=Unset)"
    >>> user.age = 27
    >>> repr(user)
    "User(name='Bob', email='bob@example.com', age=27)"

The order of fields in model's textual representation is always the same as
order in which the fields were declared in a model class.

Checking if two model objects are equal
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Modelity, two model objects are equal if an only if:

* both are instances of the same model class,
* both have same fields set,
* all fields are set to equal values.

For example:

.. testcode::

    from modelity.model import Model

    class A(Model):
        pass

    class B(Model):
        pass

    class C(Model):
        a: int
        b: int
        c: int

.. doctest::

    >>> A() != B()  # not equal; two different types
    True
    >>> A() == A()  # equal; same type, same fields set (which is none in this case)
    True
    >>> C(a=1) != C()  # not equal; different fields set
    True
    >>> C(a=1, b=2, c=3) == C(a=1, b=2, c=3)  # equal; same fields set to same values
    True
    >>> C(a=1) != C(a=2)  # not equal; same fields set, but not to with equal values
    True

Checking if field is set
^^^^^^^^^^^^^^^^^^^^^^^^

The simplest and fastest way of checking if field is set is to compare field's
value with :obj:`modelity.unset.Unset` sentinel:

.. doctest::

    >>> from modelity.unset import Unset
    >>> bob = User(name='Bob')
    >>> bob.name is Unset
    False
    >>> bob.email is Unset
    True

Since Modelity always initializes all fields, this approach will never raise
any exception for as long as existing model field is accessed. Alternatively,
you can use ``in`` operator:

.. doctest::

    >>> 'name' in bob
    True
    >>> 'email' in bob
    False

This works exactly the same as direct attribute access, but can be used safely
with non-existing fields:

.. doctest::

    >>> 'non_existing_field' in bob
    False

.. note::

    There also is a :func:`modelity.helpers.has_fields_set` helper available to
    check if model object has at least one field set.

Iterating over model object
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Model objects are iterable. Iterating over models yields names of fields that
are set, in the order defined in model type:

.. doctest::

    >>> empty = User()
    >>> list(empty)
    []
    >>> list(bob)
    ['name']
    >>> bob.email = 'bob@example.com'
    >>> list(bob)
    ['name', 'email']

Using hooks
-----------

Modelity provides several hooks that can be used to customize data processing
in user defined models. These hooks can be found in :mod:`modelity.hooks`
module and are divided into following categories:

**Input data processing hooks**

    Field-specific hooks that are executed when field is set. These hooks are
    later subdivided into:

    **Field preprocessing hooks**

        Available via :func:`modelity.hooks.field_preprocessor` decorator.

        Used to add input data filtering to be executed before type parsing
        takes place.

    **Field postprocessing hooks**

        Available via :func:`modelity.hooks.field_postprocessor` decorator.

        Used to add field-level validation or data conversion logic to be
        executed after successful preprocessing and data parsing steps. This is
        the final step of input data parsing stage and results of these hooks
        are stored in the model as final field's value.

**Model validation hooks**

    Model- and field-specific hooks executed during validation. All validation
    hooks have access to entire model object and can freely access any field
    they want. These are subdivided into:

    **Model prevalidation hooks**

        Available via :func:`modelity.hooks.model_prevalidator` decorator.

        Executed in model-wide scope **before** any built-in validation takes
        place. Can be used to override built-in validation; if model
        prevalidator fails, further validation steps are skipped.

    **Field validation hooks**

        Available via :func:`modelity.hooks.field_validator` decorator.

        Executed only if the field has value assigned. But that is the only
        difference, as these hooks can freely access other fields if needed.

    **Location-based validation hooks**

        Available via :func:`modelity.hooks.location_validator` decorator.

        Similar to field validation hooks, but allows the caller to access
        nested field, or collection items of a model if its location suffix
        matches provided location pattern.

        .. versionadded:: 0.27.0

    **Model postvalidation hooks**

        Available via :func:`modelity.hooks.model_postvalidator` decorator.

        Similar to model prevalidation hooks, but executed **after**
        prevalidators, built-in validators and field validators.

Using ``field_preprocessor`` hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This hook can be enabled using :func:`modelity.hooks.field_preprocessor` decorator.

Preprocessing hooks can be used to filter input data and prepare it for parsing
step, or to reject certain input value types, f.e. allowing only string as the
input. Value returned by preprocessing hook is either passed as an input for
the next preprocessing hook (if any), or as an input for parsing step (in this
was the last preprocessor).

Preprocessors can signal errors either by raising :exc:`TypeError`, or by
modifying ``errors`` list and returning :obj:`modelity.unset.Unset` object.

Example 1: White characters stripping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. testcode::

    from modelity.model import Model
    from modelity.hooks import field_preprocessor

    class User(Model):
        name: str
        email: str
        age: int

        @field_preprocessor('name', 'email', 'age')  # names of fields this hook will be used for
        def _strip_white_chars(value):  # any name can be used here, but underscore prefix is recommended
            if isinstance(value, str):  # we only want to strip strings
                return value.strip()
            return value

.. doctest::

    >>> bob = User(name=' Bob ', email='bob@example.com ', age=32)  # white chars from 'user' and 'email' will be stripped
    >>> bob.name
    'Bob'
    >>> bob.email
    'bob@example.com'
    >>> bob.age
    32

Example 2: Allow only strings as inputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. testcode::

    from modelity.model import Model
    from modelity.unset import Unset
    from modelity.hooks import field_preprocessor

    class User(Model):
        name: str
        email: str
        age: int

        @field_preprocessor()  # run this hook for every field
        def _reject_non_string(errors, value):
            if not isinstance(value, str):
                raise TypeError('only strings are allowed as input')
            return value

.. doctest::

    >>> user = User()  # OK; no field is set
    >>> user.age = 27  # fail; not a string
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'User':
      age:
        only strings are allowed as input [code=modelity.EXCEPTION, value_type=int, exc_type=TypeError]
    >>> user.age = '27'  # OK
    >>> user.age
    27

Using ``field_postprocessor`` hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This hook can be enabled using :func:`modelity.hooks.field_postprocessor` decorator.

Postprocessing hooks are executed if and only if previous preprocessing (if
any) and type parsing steps were successful. Postprocessors can be used to
perform field-specific validations that needs to be executed when field is set,
or to alter data returned by parser. Postprocessors also have partial read
access to other fields (if accessed field is declared before the field for
which postprocessing is executed) and full write access to other fields.

Value returned by postprocessor is then passed as an input for the next
postprocessor (if any) or stored in the model (if this was the last
postprocessor).

Postprocessors can signal errors either by raising :exc:`TypeError`, or by
modifying ``errors`` list and returning :obj:`modelity.unset.Unset` object.

.. important::

    There is no more type checking after postprocessing execution, so pay
    attention to the value returned by each postprocessor. It is possible to
    change type of the value when postprocessors are used, but not recommended,
    as it will break the contract (user of our model may expect integer and get
    string instead, for instance).

Example 1: Data alteration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. testcode::

    import math

    from modelity.model import Model
    from modelity.hooks import field_postprocessor

    class Vec2D(Model):
        x: float
        y: float

        def length(self) -> float:
            return math.sqrt(self.x**2 + self.y**2)

        def normalized(self) -> "Vec2D":
            len = self.length()
            return Vec2D(x=self.x / len, y=self.y / len)

    class Car(Model):
        direction: Vec2D

        @field_postprocessor('direction')
        def _normalize(value):
            return value.normalized()

.. doctest::

    >>> direction = Vec2D(x=3, y=4)
    >>> direction.length()  # the length of original vector
    5.0
    >>> car = Car()
    >>> car.direction = direction  # here postprocessor is applied
    >>> car.direction.length()  # the length is now 1, as the vector was normalized
    1.0

Example 2: Enforce validation of nested models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using nested models, postprocessor can be used to automatically run
validation when field is set. This is not required, however, but we can enforce
assignment of an already valid objects only:

.. testcode::

    import math

    from modelity.model import Model
    from modelity.helpers import validate
    from modelity.hooks import field_postprocessor

    class Vec2D(Model):
        x: float
        y: float

        def length(self) -> float:
            return math.sqrt(self.x**2 + self.y**2)

        def normalized(self) -> "Vec2D":
            len = self.length()
            return Vec2D(x=self.x / len, y=self.y / len)

    class Car(Model):
        position: Vec2D
        direction: Vec2D

        @field_postprocessor()  # Run for all fields
        def _validate_vec2D(value):
            if isinstance(value, Vec2D):
                validate(value)
            return value

        @field_postprocessor('direction')  # Only 'direction' will be normalized
        def _normalize(value):
            return value.normalized()

.. doctest::

    >>> car = Car()  # OK; no field is set
    >>> car.position = Vec2D(x=0, y=0)  # OK; all required fields are set
    >>> car.position = Vec2D(x=0)  # fail; 'y' is missing
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Vec2D':
      y:
        This field is required [code=modelity.REQUIRED_MISSING]
    >>> car.direction = Vec2D(y=4)  # fail; 'x' is missing
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Vec2D':
      x:
        This field is required [code=modelity.REQUIRED_MISSING]
    >>> car.direction = Vec2D(x=3, y=4)  # OK
    >>> car.direction.length()  # Normalization postprocessor still works
    1.0

Example 3: Cross-field validation on field set
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Postprocessor can also read fields that were declared earlier and, as Modelity
processes fields in their declaration order, perform cross-field validation at
the time when field is set, not when validation is performed. For example:

.. testcode::

    from modelity.model import Model
    from modelity.unset import Unset
    from modelity.hooks import field_postprocessor

    class Account(Model):
        password: str
        repeated_password: str  # Must be declared after 'password' field

        @field_postprocessor('repeated_password')
        def _check_if_the_same(self, value):
            if self.password is Unset:
                raise TypeError("no password set")
            if self.password != value:
                raise TypeError("repeated password is incorrect")
            return value  # Don't forget to return value; otherwise None will be used!

.. doctest::

    >>> account = Account()  # OK; no field is set
    >>> account.repeated_password = 'p@ssw0rd'  # fail; postprocessor requires 'password' to be set
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Account':
      repeated_password:
        no password set [code=modelity.EXCEPTION, value_type=str, exc_type=TypeError]
    >>> account.password = 'p@ssw0rd'  # now the password is set
    >>> account.repeated_password = 'password'  # fail; the repeated password is incorrect
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Account':
      repeated_password:
        repeated password is incorrect [code=modelity.EXCEPTION, value_type=str, exc_type=TypeError]
    >>> account.repeated_password = 'p@ssw0rd'  # OK
    >>> account
    Account(password='p@ssw0rd', repeated_password='p@ssw0rd')

.. important::

    When postprocessor is used for cross-field validation it must be declared
    for field that in model class definition occurs **after** fields that are
    accessed. If that is not possible, then use model pre- or postvalidator
    instead.

Example 4: Setting other fields from postprocessor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is side-effect of making it possible to access model object from field
postprocessor. But this is quite useful side-effect, as it allows to initialize
correlated fields if no other value was given. For example, when setting
*created* time, the postprocessor can in addition set *modified* to the same
value:

.. testcode::

    import datetime

    from modelity.model import Model
    from modelity.unset import Unset
    from modelity.hooks import field_postprocessor

    class File(Model):
        modified: datetime.date
        created: datetime.date  # Must be declared after 'modified'; otherwise it may access a non-existing attribute during object construction

        @field_postprocessor('created')
        def _initialize_modified(self, value):
            if self.modified is Unset:  # don't override if already set
                self.modified = value
            return value  # Don't forget to return value

.. doctest::

    >>> foo = File(created='1999-01-01')  # just 'created' given; 'modified' is set by postprocessor
    >>> foo.created == foo.modified  # both dates are equal
    True
    >>> bar = File(created='1999-01-01', modified='2021-01-01')  # both 'created' and 'modified' given; the postprocessor won't change 'modified'
    >>> bar.created != bar.modified
    True
    >>> baz = File()  # Nothing is set
    >>> baz.created
    Unset
    >>> baz.modified
    Unset
    >>> baz.created = '1999-01-01'  # Implicitly sets 'modified'
    >>> baz.modified
    datetime.date(1999, 1, 1)


Using ``model_prevalidator`` hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This hook can be enabled using :func:`modelity.hooks.model_prevalidator` decorator.

Model prevalidation is first step of model validation, happening just before
built-in validators and required field presence checking. Model prevalidators
can access all fields of the model they are declared in, therefore it is
capable of performing cross-field validation easily.

Example 1: Cross-field validation on per-model basis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's assume we have a model with two fields and we need to check cross-field
dependencies on a per-model basis. Here's an example:

.. testcode::

    from modelity.model import Model
    from modelity.helpers import validate
    from modelity.unset import Unset
    from modelity.hooks import model_prevalidator

    class Example(Model):
        colors_available: list[str] = ['red', 'green', 'blue']
        color_selected: str

        @model_prevalidator()
        def _check_color_selected(self):
            if self.color_selected not in self.colors_available:
                raise ValueError(f"unsupported color: {self.color_selected}")

.. doctest::

    >>> obj = Example()
    >>> obj.color_selected = 'red'
    >>> validate(obj)  # OK; existing color given
    >>> obj.color_selected = 'black'
    >>> validate(obj)  # failure; wrong color given
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Example':
      (empty):
        unsupported color: black [code=modelity.EXCEPTION, exc_type=ValueError]


Example 2: Validation skipping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's check what will happen if we validate the model from previous example
without setting **color_selected** field:

.. doctest::

    >>> obj = Example()
    >>> validate(obj)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 2 validation errors for model 'Example':
      (empty):
        unsupported color: Unset [code=modelity.EXCEPTION, exc_type=ValueError]
      color_selected:
        This field is required [code=modelity.REQUIRED_MISSING]

As you can see, our custom model prevalidator was executed along with the
built-in required field check. In this case this is kind of redundant error, so
let's fix it by disabling built-in validation. To do so, we have to modify our
original model prevalidator to add error manually and return ``True`` from it
to skip other validators:

.. testcode::

    from modelity.model import Model
    from modelity.error import Error
    from modelity.loc import Loc
    from modelity.helpers import validate
    from modelity.unset import Unset
    from modelity.hooks import model_prevalidator

    class Example(Model):
        colors_available: list[str] = ['red', 'green', 'blue']
        color_selected: str

        @model_prevalidator()
        def _check_color_selected(self, errors, loc):  # `errors` and `loc` are needed to create error
            if self.color_selected not in self.colors_available:
                # Create custom error and add it to the errors list.
                # This is RECOMMENDED way of creating custom errors, as it
                # gives full access to Error constructor allowing to set both
                # custom error message, custom error code, and error location.
                errors.append(
                    Error(
                        loc + Loc('color_selected'),  # error location; we can point to the actual field if needed
                        "custom.INVALID_VALUE",  # custom error code
                        f"unsupported color: {self.color_selected}",  # custom error message
                        self.color_selected  # the current incorrect value
                    )
                )
            return True  # No more validators will be called for this model

And now, there will only be a single error:

.. doctest::

    >>> obj = Example()
    >>> validate(obj)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Example':
      color_selected:
        unsupported color: Unset [code=custom.INVALID_VALUE]


And of course, if valid value is given, then validation will pass:

.. doctest::

    >>> obj = Example(color_selected='red')
    >>> validate(obj)  # OK

.. important::

    Please note that we had to create error manually to force model
    prevalidation to return ``True``. If fact, this is RECOMMENDED way of
    creating custom errors; raising exceptions is just a shortcut.

Using ``field_validator`` hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This hook can be enabled using :func:`modelity.hooks.field_validator` decorator.

Field validators are executed for selected fields only and only if the field
has value set. It should be used to verify if validated field has correct data
by comparing it in user-defined way with one or more other fields in the model.
Also, unlike model-level validators, the error location is filled to point to
the validated field, not entire model.

For example:

.. testcode::

    from modelity.model import Model
    from modelity.hooks import field_validator
    from modelity.helpers import validate

    class User(Model):
        email: str
        repeated_email: str

        @field_validator('repeated_email')
        def _check_if_the_same(self, value):
            if self.email != value:
                raise ValueError('incorrect repeated e-mail address')

.. doctest::

    >>> bob = User()
    >>> validate(bob)  # fail; required fields are missing
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 2 validation errors for model 'User':
      email:
        This field is required [code=modelity.REQUIRED_MISSING]
      repeated_email:
        This field is required [code=modelity.REQUIRED_MISSING]
    >>> bob.email = 'bob@example.com'
    >>> validate(bob)  # fail; 'repeated_email' is missing
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'User':
      repeated_email:
        This field is required [code=modelity.REQUIRED_MISSING]
    >>> bob.repeated_email = 'bob@example.com'
    >>> validate(bob)  # OK
    >>> alice = User(email='alice@example.com', repeated_email='bob@example.com')
    >>> validate(alice)  # fail; emails are not equal
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'User':
      repeated_email:
        incorrect repeated e-mail address [code=modelity.EXCEPTION, exc_type=ValueError]


Using ``location_validator`` hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 0.27.0

This hook can be enabled using :func:`modelity.hooks.location_validator` decorator.

It allows to access fields of a nested model, or individual collection items
directly from model validator. This allows to add complex validation logic
based on nested fields with no need to alter existing nested models. Thanks to
this, same model can be used in different situations, with different validation
requirements defined for each.

Here's an example:

.. testcode::

    from typing import Optional

    from modelity.model import Model
    from modelity.hooks import location_validator
    from modelity.helpers import validate

    class User(Model):
        email: str
        name: Optional[str] = None

    class Storage(Model):
        users: list[User]

        @location_validator("users.*")
        def _require_name(value):
            if not value.name:
                raise ValueError("stored users must have name assigned")

.. doctest::

    >>> bob = User(email="bob@example.com")
    >>> accounts = Storage(users=[bob])
    >>> validate(bob)  # OK; `name` is optional
    >>> validate(accounts)  # FAIL; here `name` is required by location validator
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Storage':
      users.0:
        stored users must have name assigned [code=modelity.EXCEPTION, exc_type=ValueError]


As you can see, `name` is optional as a part of **User**, but becomes required
when user is used as an item in `users` list.

Using ``model_postvalidator`` hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This hook can be enabled using :func:`modelity.hooks.model_postvalidator` decorator.

Model postvalidators are executed after all other validators and are best way
to perform cross-field checks in the model scope. For example, let's rewrite
example from above to use model postvalidator instead:

.. testcode::

    from modelity.model import Model
    from modelity.unset import Unset
    from modelity.hooks import model_postvalidator
    from modelity.helpers import validate

    class User(Model):
        email: str
        repeated_email: str

        @model_postvalidator()
        def _check_if_emails_match(self):
            if self.email is Unset or self.repeated_email is Unset:
                return
            if self.email != self.repeated_email:
                raise ValueError("the 'email' field does not match 'repeated_email' field")

.. doctest::

    >>> john = User(email='john@example.com', repeated_email='John@example.com')
    >>> validate(john)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'User':
      (empty):
        the 'email' field does not match 'repeated_email' field [code=modelity.EXCEPTION, exc_type=ValueError]

Please note, that postvalidator runs in the model scope, therefore error
location points to the model. It is empty, because the model is the root model.
For nested model, the error would point to a field in a parent model instead:

.. testcode::

    class UserStore(Model):
        users: list[User]

.. doctest::

    >>> store = UserStore()
    >>> store.users = [User(email='john@example.com', repeated_email='JOHN@example.com')]
    >>> validate(store)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'UserStore':
      users.0:
        the 'email' field does not match 'repeated_email' field [code=modelity.EXCEPTION, exc_type=ValueError]


Reporting errors from user-defined hooks
----------------------------------------

By raising ``TypeError``
^^^^^^^^^^^^^^^^^^^^^^^^

When :exc:`TypeError` is raised by any of the following hooks:

* :func:`modelity.hooks.field_preprocessor`
* :func:`modelity.hooks.field_postprocessor`

then it is intercepted by Modelity and converted into
:class:`modelity.error.Error` object and attached to
:exc:`modelity.exc.ParsingError` exception.

For example:

.. testcode::

    from modelity.api import Model, field_preprocessor

    class Dummy(Model):
        foo: int

        @field_preprocessor()
        def _ensure_string(value):
            if not isinstance(value, str):
                raise TypeError("Only strings are accepted")
            return value

.. doctest::

    >>> dummy = Dummy()
    >>> dummy.foo = "123"  # OK
    >>> dummy.foo
    123
    >>> dummy.foo = 123  # FAIL; for some reason we want all input to be string
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Dummy':
      foo:
        Only strings are accepted [code=modelity.EXCEPTION, value_type=int, exc_type=TypeError]

By raising ``ValueError``
^^^^^^^^^^^^^^^^^^^^^^^^^

When :exc:`ValueError` is raised by any of the following hooks:

* :func:`modelity.hooks.model_prevalidator`
* :func:`modelity.hooks.model_postvalidator`
* :func:`modelity.hooks.field_validator`
* :func:`modelity.hooks.location_validator`

then it is intercepted by Modelity and converted into
:class:`modelity.error.Error` object and attached to
:exc:`modelity.exc.ValidationError` exception.

For example:

.. testcode::

    from modelity.api import Model, field_preprocessor, StrictOptional, Unset, validate

    class Dummy(Model):
        foo: StrictOptional[int]
        bar: StrictOptional[int]

        @model_prevalidator()
        def _ensure_either_foo_or_bar(self):
            if self.foo is not Unset and self.bar is not Unset:
                raise ValueError("Either `foo` or `bar` can be set, not both")

.. doctest::

    >>> dummy = Dummy()
    >>> validate(dummy)  # OK; both are optional
    >>> dummy.foo = 123
    >>> validate(dummy)  # OK; just `foo` given so far
    >>> dummy.bar = 456
    >>> validate(dummy)  # FAIL; both given
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'Dummy':
      (empty):
        Either `foo` or `bar` can be set, not both [code=modelity.EXCEPTION, exc_type=ValueError]

By raising ``modelity.exc.UserError``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 0.30.0

This is the most generic way of reporting errors from user-defined hooks. It
can be used by any hook and, depending on the hook type, will result in an
:class:`modelity.error.Error` object being attached to either
:exc:`modelity.exc.ParsingError` or :exc:`modelity.exc.ValidationError`
exception.

For example:

   .. testcode::

    from modelity.api import Model, field_validator, validate, UserError

    class User(Model):
        email: str
        repeated_email: str

        @field_validator("repeated_email")
        def _check_if_repeated_same(self, value):
            if self.email != value:
                raise UserError("Repeated e-mail does not match e-mail", data={'email': self.email, 'repeated_email': value})

.. doctest::

    >>> user = User(email="jd@example.com", repeated_email="j.d@example.com")
    >>> validate(user)  # FAIL
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'User':
      repeated_email:
        Repeated e-mail does not match e-mail [code=modelity.USER_ERROR, email='jd@example.com', repeated_email='j.d@example.com']

Check :exc:`modelity.exc.UserError` docs for more options.

By manually modifying ``errors`` list
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the most generic way of reporting errors. You basically create
:class:`modelity.error.Error` objects by hand and manually adding it to
``errors`` list.

For example:

.. testcode::

    from modelity.api import Model, Error, field_preprocessor

    class Dummy(Model):
        foo: int

        @field_preprocessor()
        def _ensure_string(errors: list[Error], loc, value):
            if not isinstance(value, str):
                errors.append(Error(loc, "user.USER_ERROR", "Only strings are accepted", value, data={"given_type": type(value)}))
                return Unset
            return value

.. doctest::

    >>> dummy = Dummy()
    >>> dummy.foo = 123
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Dummy':
      foo:
        Only strings are accepted [code=user.USER_ERROR, value_type=int, given_type=int]

This is the most verbose way of reporting errors, but it also offers the
greatest flexibility for customization. For example, you can easily modify
location of the error.

Check :exc:`modelity.error.Error` for the list of options available.

.. tip::

   Since ``errors`` list is mutable and shared across all hooks when parsing or
   validating, you can also *remove* errors from the list if needed. This is
   especially useful with :func:`modelity.hooks.model_postvalidator` hook that
   runs after all other validation hooks defined for a model.

Customizing type parsers
------------------------

Some of the built-in Modelity type parsers can be customized via so called
**type options**. These options can be set using keyword arguments of
:func:`modelity.model.field_info` helper function, or directly, via
:attr:`modelity.model.FieldInfo.type_opts` attribute.

bool
^^^^

Options available:

``true_literals: list[Any]``
    The list of literals evaluating to ``True``.

``false_literals: list[Any]``
    The list of literals evaluating to ``False``.

Example:

.. testcode::

    from modelity.model import Model, field_info

    class BoolExample(Model):
        foo: bool = field_info(true_literals=['on'], false_literals=['off'])

.. doctest::

    >>> obj = BoolExample()
    >>> obj.foo = True  # as usual; assign boolean
    >>> obj.foo
    True
    >>> obj.foo = 'on'  # this would fail without type options
    >>> obj.foo
    True
    >>> obj.foo = 'off'  # this would fail without type options
    >>> obj.foo
    False

datetime.datetime
^^^^^^^^^^^^^^^^^

Options available:

``input_datetime_formats: list[str]``
    The list of input datetime formats.

    Every string that matches one of these formats will be successfully parsed
    as a datetime object.

    Following placeholders are available:

    * **YYYY** - 4-digit year number,
    * **MM** - 2-digit month number (01..12),
    * **DD** - 2-digit day number (01..31),
    * **hh** - 2-digit hour (00..23)
    * **mm** - 2-digit minute (00..59)
    * **ss** - 2-digit second (00-59)
    * **ZZZZ** - timezone (f.e. +0200)

``output_datetime_format: str``
    The format to use when datetime object is formatted as string.

    Same placeholders are used as for ``input_datetime_formats``.

Example:

.. testcode::

    import datetime

    from modelity.model import Model, field_info

    class DateTimeExample(Model):
        foo: datetime.datetime = field_info(
            input_datetime_formats=['YYYY-MM-DD hh:mm:ss', 'YYYY-MM-DD'],
            output_datetime_format='DD-MM-YYYY hh:mm:ss'
        )

.. doctest::

    >>> obj = DateTimeExample()
    >>> obj.foo = '1999-01-02 11:22:33'  # OK
    >>> obj.foo
    datetime.datetime(1999, 1, 2, 11, 22, 33)
    >>> obj.foo = '2025-01-03'  # OK
    >>> obj.foo
    datetime.datetime(2025, 1, 3, 0, 0)
    >>> obj.foo = '02-01-1999'  # fail; does not match any of the input formats
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'DateTimeExample':
      foo:
        Not a valid datetime format; expected one of: YYYY-MM-DD hh:mm:ss, YYYY-MM-DD [code=modelity.INVALID_DATETIME_FORMAT, value_type=str, expected_formats=['YYYY-MM-DD hh:mm:ss', 'YYYY-MM-DD']]

.. doctest::

    >>> from modelity.helpers import dump
    >>> obj.foo = '2025-01-02 11:22:33'
    >>> obj.foo
    datetime.datetime(2025, 1, 2, 11, 22, 33)
    >>> dump(obj)  # `output_datetime_format` will be used
    {'foo': '02-01-2025 11:22:33'}

datetime.date
^^^^^^^^^^^^^

Options available:

``input_date_formats: list[str]``
    The list of input date formats.

    Every string that matches one of these formats will be successfully parsed
    as a datet object.

    Following placeholders are available:

    * **YYYY** - 4-digit year number,
    * **MM** - 2-digit month number (01..12),
    * **DD** - 2-digit day number (01..31),

``output_date_format: str``
    The format to use when date object is formatted as string.

    Same placeholders are used as for ``input_date_formats``.

Example:

.. testcode::

    import datetime

    from modelity.model import Model, field_info

    class DateExample(Model):
        foo: datetime.date = field_info(
            input_date_formats=['YYYY-MM-DD', 'DD-MM-YYYY'],
            output_date_format='YYYY-MM-DD'
        )

.. doctest::

    >>> obj = DateExample()
    >>> obj.foo = '1999-01-02'  # OK
    >>> obj.foo
    datetime.date(1999, 1, 2)
    >>> obj.foo = '02-03-2025'  # OK
    >>> obj.foo
    datetime.date(2025, 3, 2)
    >>> obj.foo = '02-01-1999 11:22:33'  # fail; does not match any of the input formats
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'DateExample':
      foo:
        Not a valid date format; expected one of: YYYY-MM-DD, DD-MM-YYYY [code=modelity.INVALID_DATE_FORMAT, value_type=str, expected_formats=['YYYY-MM-DD', 'DD-MM-YYYY']]

.. doctest::

    >>> from modelity.helpers import dump
    >>> obj.foo = '2025-01-02'
    >>> obj.foo
    datetime.date(2025, 1, 2)
    >>> dump(obj)  # `output_date_format` will be used
    {'foo': '2025-01-02'}

pathlib.Path
^^^^^^^^^^^^

Options available:

``bytes_encoding: str = 'utf-8'``
    Encoding to use when parsing path given as bytes object.

    Defaults to UTF-8.

Example:

.. testcode::

    import pathlib

    from modelity.model import Model, field_info

    class PosixPathExample(Model):
        foo: pathlib.Path = field_info(bytes_encoding='ascii')

.. doctest::

    >>> obj = PosixPathExample()
    >>> obj.foo = b'\xff'  # fail; ascii codec can't decode this
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'PosixPathExample':
      foo:
        Invalid text encoding [code=modelity.DECODE_ERROR, value_type=bytes, expected_encodings=['ascii']]

.. doctest::

    >>> from modelity.helpers import dump
    >>> obj.foo = '/tmp/some/file.txt'  # this will pass
    >>> obj.foo
    PosixPath('/tmp/some/file.txt')
