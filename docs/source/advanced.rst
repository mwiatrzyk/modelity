Advanced user's guide
=====================

Registering custom types
------------------------

Let's try to use the following type in our model:

.. testcode::

    import dataclasses

    @dataclasses.dataclass
    class Vec2D:
        x: float
        y: float

Since Modelity does not known how to parse this type,
:exc:`modelity.exc.UnsupportedTypeError` exception will be raised during model
declaration:

.. doctest::

    >>> from modelity.model import Model
    >>> class Car(Model):
    ...     position: Vec2D
    Traceback (most recent call last):
      ...
    modelity.exc.UnsupportedTypeError: unsupported type used: <class 'Vec2D'>

To overcome this obstacle, Modelity provides 2 possibilities that will be
explained in the upcoming sections.

Using ``__modelity_type_descriptor__`` static method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To make it possible to use **Vec2D** in our model, we can add Modelity-specific
static method that will provide a type descriptor for **Vec2D** type:

.. testcode::

    import dataclasses

    from modelity.interface import ITypeDescriptor
    from modelity.error import ErrorFactory


    @dataclasses.dataclass
    class Vec2D:
        x: float
        y: float

        @staticmethod
        def __modelity_type_descriptor__():
            return Vec2DTypeDescriptor()


    class Vec2DTypeDescriptor(ITypeDescriptor):

        # Parsing logic goes in here
        def parse(self, errors, loc, value):
            if isinstance(value, Vec2D):
                return value  # Nothing is changed for Vec2D objects
            if isinstance(value, tuple) and len(value) == 2:
                return Vec2D(*value)  # Convert from tuple
            errors.append(ErrorFactory.invalid_type(loc, value, [Vec2D], [Vec2D, tuple[float, float]]))

        # Visitor accepting logic goes in here
        # Choose best suited method here, depending on which one is closest to
        # the type that is being registered
        def accept(self, visitor, loc, value):
            visitor.visit_any(loc, [value.x, value.y])  # will be dumped/validated as 2-element list

And now, let's create the model again:

.. testcode::

    from modelity.model import Model

    class Car(Model):
        position: Vec2D

Now there is no exception, as Modelity knows (thanks to the
``__modelity_type_descriptor__`` method) how to create type descriptor for our
type.

Now, let's see this in action:

.. doctest::

    >>> car = Car()  # OK; nothing is set
    >>> car.position = Vec2D(1, 2)  # OK; the exact type used
    >>> car.position
    Vec2D(x=1, y=2)
    >>> car.position = (3, 4)  # OK; we've made is possible to cast from tuple
    >>> car.position
    Vec2D(x=3, y=4)
    >>> car.position = 'spam'  # fail; not Vec2D, 2-element tuple or dict
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Car':
      position:
        Not a valid value; expected a Vec2D [code=modelity.INVALID_TYPE, value_type=str, expected_types=[Vec2D], allowed_types=[Vec2D, tuple[float, float]]]


Using ``type_descriptor_factory`` decorator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also use :func:`modelity.hooks.type_descriptor_factory` decorator to
register new type. This is especially useful for 3rd-party types that cannot
have ``__modelity_type_descriptor__`` static method added.

Here's a definition of a **Vec3D** type:

.. testcode::

    import dataclasses

    @dataclasses.dataclass
    class Vec3D:
        x: float
        y: float
        z: float

To tell Modelity how to use this type without modifying it and adding
additional methods you have to declare type descriptor factory and return a
descriptor object similar to the one from the previous example:

.. testcode::

    from modelity.hooks import type_descriptor_factory
    from modelity.error import ErrorFactory
    from modelity.interface import ITypeDescriptor

    @type_descriptor_factory(Vec3D)
    def make_vec3d_descriptor():

        class Descriptor(ITypeDescriptor):

            def parse(self, errors, loc, value):
                if isinstance(value, Vec3D):
                    return value
                if isinstance(value, tuple) and len(value) == 3:
                    return Vec3D(*value)
                errors.append(ErrorFactory.unsupported_value_type(loc, value, "expecting Vec3D or 3-element tuple", [Vec2D, tuple]))

            def accept(self, visitor, loc, value):
                visitor.visit_any(loc, [value.x, value.y, value.z])  # will be dumped/validated as 3-element list

        return Descriptor()

And now, Modelity will be able to use this new type:

.. testcode::

    from modelity.model import Model

    class Camera(Model):
        pos: Vec3D
        direction: Vec3D

.. doctest::

    >>> from modelity.helpers import dump
    >>> cam = Camera(pos=(1, 2, 3), direction=(0, 0, 1))  # OK; tuples will be converted, as in previous example
    >>> cam
    Camera(pos=Vec3D(x=1, y=2, z=3), direction=Vec3D(x=0, y=0, z=1))
    >>> dump(cam)
    {'pos': [1, 2, 3], 'direction': [0, 0, 1]}

Reusing existing type descriptors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In examples presented above we did not check if coordinates are valid float
numbers. As a result, passing string will not fail, because coordinates are not
parsed, but passed in original form:

.. doctest::

    >>> cam.pos = (1, 2, 'spam')
    >>> cam.pos
    Vec3D(x=1, y=2, z='spam')

If needed, this can be fixed to also allow checking if coordinates are valid
float numbers. Here's a definition of **Vec3D** type descriptor that
additionally parses coordinates as float numbers:

.. testcode::

    from modelity.hooks import type_descriptor_factory
    from modelity.loc import Loc
    from modelity.error import ErrorFactory
    from modelity.interface import ITypeDescriptor
    from modelity.model import Model

    @type_descriptor_factory(Vec3D)
    def make_vec3d_descriptor(make_type_descriptor):  # Declare the use of root type descriptor factory

        class Descriptor(ITypeDescriptor):

            def parse(self, errors, loc, value):
                if isinstance(value, Vec3D):
                    return Vec3D(*parse_coords(errors, loc, value.x, value.y, value.z))
                if isinstance(value, tuple) and len(value) == 3:
                    return Vec3D(*parse_coords(errors, loc, *value))
                errors.append(ErrorFactory.unsupported_value_type(loc, value, "expecting Vec3D or 3-element tuple", [Vec2D, tuple]))

            def accept(self, visitor, loc, value):
                visitor.visit_any(loc, [value.x, value.y, value.z])  # will be dumped/validated as 3-element list

        # Helper function
        def parse_coords(errors, loc, *coords):
            for name, value in zip(('x', 'y', 'z'), coords):
                yield float_descriptor.parse(errors, loc + Loc(name), value)

        float_descriptor = make_type_descriptor(float)  # Get type descriptor for float type
        return Descriptor()

    class Camera(Model):
        pos: Vec3D
        direction: Vec3D

And since now, assigning *pos* or *direction* will also parse each single
coordinate:

.. doctest::

    >>> cam = Camera()
    >>> cam.pos = '1', '2', '3'  # OK; coords will be converted to float
    >>> cam.pos
    Vec3D(x=1.0, y=2.0, z=3.0)
    >>> cam.direction = Vec3D(0, 0, 1)  # OK; coords will be converted to float
    >>> cam.direction
    Vec3D(x=0.0, y=0.0, z=1.0)
    >>> cam.direction = 0, 1, 'spam'  # fail; at coordinate z; not a float number
    Traceback (most recent call last):
      ...
    modelity.exc.ParsingError: Found 1 parsing error for type 'Camera':
      direction.z:
        Not a valid float value [code=modelity.PARSE_ERROR, value_type=str, expected_type=float]

Advanced validation patterns
----------------------------

Accessing entire model tree from nested model's validator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Modelity, it is possible to perform nested model validation that depends
on some properties defined in the parent model, or in another nested model.
For example, we can have the list of forbidden logins declared in the root
model, and a validator in child model that checks if the login is forbidden
or not:

.. testcode::

    from modelity.model import Model
    from modelity.helpers import validate
    from modelity.hooks import field_validator

    class User(Model):
        login: str

        @field_validator('login')
        def _validate_login(root, value):  # root - validated model, value - current login
            if isinstance(root, UserStore):  # execute only when User is part of UserStore
                if value in root.logins_forbidden:
                    raise ValueError(f'the login is forbidden: {value}')

    class UserStore(Model):
        logins_forbidden: list[str]
        users: list[User]

.. doctest::

    >>> store = UserStore(logins_forbidden=['foo'], users=[])
    >>> store.users.append(User(login='spam'))  # OK
    >>> store.users.append(User(login='foo'))  # will not fail here, but login is forbidden
    >>> validate(store)  # 'store' is the root model for validators
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'UserStore':
      users.1.login:
        the login is forbidden: foo [code=modelity.EXCEPTION, exc_type=ValueError]


Why not validating such or similar cases inside **UserStore** object?

Well, that depends on what kind of errors you want to receive. In the
example above, the error is related to the **User** model, therefore it
will be duplicated if more such objects are added to the list, producing a more
verbose error report:

.. doctest::

    >>> store.logins_forbidden.append('bar')
    >>> store.users.append(User(login='bar'))  # 'bar' is also forbidden
    >>> validate(store)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 2 validation errors for model 'UserStore':
      users.1.login:
        the login is forbidden: foo [code=modelity.EXCEPTION, exc_type=ValueError]
      users.2.login:
        the login is forbidden: bar [code=modelity.EXCEPTION, exc_type=ValueError]


If you need single combined error, then it would be better to validate
inside **UserStore** instead.

.. important::

    Choose carefully when to validate inside child model, and when to
    validate inside parent model. Although both have their pros and cons,
    accessing parent model from a child model provides direct dependency
    towards parent model.

Validating with user-defined context
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modelity allows the user to provide context object for validators. This object
is completely invisible to Modelity, so it can be of any type. The only thing
that Modelity does is to pass this object to every single validator that is
defined for a model, or nested models.

What this context can be used for? Let's imagine a situation in which you have
to validate your model against some data fetched from a database. If this
fetched data is set somewhere in the model, then you just can go to the
previous chapter. But if you don't want, or you cannot set such data in the
model, then contexts come into play.

For example, let's embed checking for login availability into Modelity
validators:

.. testcode::

    from modelity.model import Model
    from modelity.hooks import field_validator

    class UserValidationContext:  # Anything can be used as validation context

        def __init__(self, user_repository):
            self._user_repository = user_repository

        def is_login_available(self, login) -> bool:  # Yes, we can also use methods
            return login not in self._user_repository

    class User(Model):
        login: str
        password: str

        @field_validator("login")
        def _check_if_available(ctx, value):  # You have to declare 'ctx' argument to enable context access
            if not ctx.is_login_available(value):  # Call the method from context
                raise ValueError(f"login already in use: {value}")  # Fail validation if login is in use

.. doctest::

    >>> from modelity.helpers import validate
    >>> user_repository = ['joe', 'alice']  # This is just an example
    >>> ctx = UserValidationContext(user_repository)  # Create context
    >>> joe = User(login='joe', password='p@ssw0rd')
    >>> alice = User(login='alice', password='p@ssw0rd')
    >>> validate(joe, ctx)  # Validation with context will fail for 'joe'...
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'User':
      login:
        login already in use: joe [code=modelity.EXCEPTION, exc_type=ValueError]
    >>> validate(alice, ctx)  # ...or 'alice'
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: Found 1 validation error for model 'User':
      login:
        login already in use: alice [code=modelity.EXCEPTION, exc_type=ValueError]
    >>> jack = User(login='jack', password='password')
    >>> validate(jack, ctx)  # But will succeed for jack

Thanks to context objects you can easily integrate Modelity validators with
your application's business logic to achieve one central validation mechanism
based on models. Also, contexts can only be used by user-defined validators,
therefore using context does not affect Modelity's built-in mechanisms.

Hook inheritance
----------------

Declaring base model with common hooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When using hooks you will declare hook directly in the model class for most
cases. However, sometimes same hook needs to be provided for other models as
well. Consider this example:

.. testcode::

    from modelity.model import Model
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

    from modelity.model import Model
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

    from modelity.model import Model
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

    from modelity.model import Model
    from modelity.hooks import field_preprocessor


    class StringStrippingMixin:  # this is a mixin; we don't inherit from model

        @field_preprocessor()  # use this hook for any field...
        def _strip_string(value):  # ...especially if we don't use it for any particular field
            if isinstance(value, str):
                return value.strip()
            return value


    class Base(Model, StringStrippingMixin):  # base class for First and Second; both will use the mixin
        pass


    class First(Base):
        foo: str


    class Second(Base):
        bar: str


    class Third(Model):  # Here we don't use our mixin...
        baz: str


    class Fourth(Third, StringStrippingMixin):  # ...and here we do
        spam: str

And the final check looks as follows:

.. doctest::

    >>> first = First(foo=" 123")
    >>> second = Second(bar="456 ")
    >>> third = Third(baz=" 789 ")
    >>> fourth = Fourth(spam=' spam ')
    >>> first.foo, second.bar, third.baz, fourth.spam
    ('123', '456', ' 789 ', 'spam')
