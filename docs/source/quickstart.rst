Quickstart
==========

Declaring model types
---------------------

In Modelity, models are declared by creating a subclass of
:class:`modelity.model.Model` base class and declaring fields via type
annotations:

.. testcode::

    from modelity.model import Model

    class Book(Model):
        title: str
        author: str
        publisher: str
        year: int

It is also possible to use helpers from :mod:`typing` module. For example, we
can create a model ``Bookstore`` that will be able to store list of ``Book``
model items. Let's additionally make that field optional:

.. testcode::

    from typing import List, Optional

    class Bookstore(Model):
        books: Optional[List[Book]]

Creating model instances
------------------------

Using constructor
^^^^^^^^^^^^^^^^^

To create instance of a model, you have to use constructor of the created model
class. Constructor can only be called with named arguments. Modelity will
iterate through the list of fields and parse arguments having same name. Any
extra arguments will be ignored:

.. testcode::

    first = Book(
        title="My First Book",
        author="John Doe",
        publisher="Imaginary Publishing",
        year=2024,
        extra_argument="spam"
    )
    print(first)

After executing code from above, following will be printed:

.. testoutput::

    Book(title='My First Book', author='John Doe', publisher='Imaginary Publishing', year=2024)

Modelity verifies presence of required fields at validation phase, not during
data parsing, therefore it allows to create models that can be initialized
later, for example by prompting the user:

.. testcode::
    :hide:

    def prompt(msg):
        return "My Second Book"

.. testcode::

    second = Book()  # Will not fail
    second.title = prompt("Book title:")  # User enters: My Second Book
    print(second)

And here's what will be printed:

.. testoutput::

    Book(title='My Second Book', author=Unset, publisher=Unset, year=Unset)

As you can see, only one field was set, all other remain ``Unset``. And
``Unset`` is a special value (instance of :class:`modelity.unset.UnsetType`
class) used to distinguish unset fields from fields that are set to ``None``.

Using ``load`` method
^^^^^^^^^^^^^^^^^^^^^

It is also possible to create model instances directly from dicts using
:meth:`modelity.model.Model.load` method:

.. testcode::

    third = Book.load({"title": "My Third Book"})
    print(third)

.. testoutput::

    Book(title='My Third Book', author=Unset, publisher=Unset, year=Unset)

Under the hood this method does nothing but constructor calling, therefore its
behavior is exactly the same as for constructor described above.

Using ``load_valid`` method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If for any reason you need to create an already valid model, you can use
:meth:`modelity.model.Model.load_valid` method:

.. testcode::

    fourth = Book.load_valid({
        "title": "My 4th Book",
        "author": "John Doe",
        "publisher": "Imaginary Publishing",
        "year": 2024,
    })
    print(fourth)

.. testoutput::

    Book(title='My 4th Book', author='John Doe', publisher='Imaginary Publishing', year=2024)

This method calls the constructor with provided params, and runs validation
shortly after. Model created in the example above is already valid, as it was
created with all required fields given. However, creating model using this
method with no parameters given will result in a validation error, as all
required fields are missing:

.. doctest::

    >>> Book.load_valid({})
    Traceback (most recent call last):
        ...
    modelity.exc.ValidationError: validation of model 'Book' failed with 4 error(-s):
      author:
        modelity.RequiredMissing {}
      publisher:
        modelity.RequiredMissing {}
      title:
        modelity.RequiredMissing {}
      year:
        modelity.RequiredMissing {}

Setting and getting fields
--------------------------

Let's create uninitialized ``Book`` instance, giving it no parameters:

.. testcode::

    book = Book()

Modelity will not fail if you give no arguments, as checking if required fields
are set is done during validation step, that must be executed explicitly. So
let's now set some fields on the model we've created:

.. doctest::

    >>> book.author = "John Doe"
    >>> book.title = "Yet Another Book"
    >>> book.author
    'John Doe'
    >>> book.title
    'Yet Another Book'

The fields are set successfully, because we've used correct type. However, if
we try to set ``book.author`` to, f.e. integer number, then parser will
complain about it by raising :exc:`modelity.exc.ParsingError` exception:

.. doctest::

    >>> book.author = 1
    Traceback (most recent call last):
        ...
    modelity.exc.ParsingError: parsing failed with 1 error(-s):
      author:
        modelity.StringRequired {}

And the field will still have previous value set:

.. doctest::

    >>> book.author
    'John Doe'

The exception, however, will not be always raised, as for some types coercion
is performed and if it is possible to convert user input to correct type, then
such coercion will take place seamlessly:

.. doctest::

    >>> book.year = "2024"
    >>> book.year
    2024

Getting an unset fields
-----------------------

Modelity will never raise :exc:`AttributeError` for unset fields, but instead
it will return ``Unset`` for such fields. For example, we did not set
``publisher`` field, so getting it will return ``Unset``:

.. doctest::

    >>> book.publisher
    Unset

However, if we try to get attribute that is not model's field, then we will get
:exc:`AttributeError` exception:

.. doctest::

    >>> book.spam
    Traceback (most recent call last):
        ...
    AttributeError: 'Book' object has no attribute 'spam'

Setting non-field attributes
----------------------------

When you try to set attribute that is not declared as model's field, then
following error will be raised:

.. doctest::

    >>> book.spam = 123
    Traceback (most recent call last):
        ...
    AttributeError: 'Book' model has no field named 'spam'

Deleting fields
---------------

Once field is set on a model, it can be deleted, i.e. restored to the ``Unset``
state. You can do this explicitly, by setting ``Unset``, or via :func:`delattr`
function. For example:

.. doctest::

    >>> from modelity.unset import Unset
    >>> book
    Book(title='Yet Another Book', author='John Doe', publisher=Unset, year=2024)
    >>> book.title = Unset
    >>> book
    Book(title=Unset, author='John Doe', publisher=Unset, year=2024)
    >>> delattr(book, 'author')
    >>> book
    Book(title=Unset, author=Unset, publisher=Unset, year=2024)

Checking if field is set
------------------------

Modelity allows to check if field is set by either comparing with ``Unset``
value, or by using ``in`` operator:

.. doctest::

    >>> book = Book(author="John Doe")
    >>> book.title == Unset
    True
    >>> book.author != Unset
    True
    >>> "title" in book
    False
    >>> "author" in book
    True

Iterating over available fields
-------------------------------

To iterate over all available model fields, you have to use
:attr:`modelity.model.ModelMeta.__fields__` dict that is available for
model classes (not instances):

.. doctest::

    >>> list(Book.__fields__)
    ['title', 'author', 'publisher', 'year']

The fields are iterated in their declaration order. You can additionally use
this attribute to access :class:`modelity.field.BoundField` objects describing
fields:

.. doctest::

    >>> Book.__fields__["title"]
    <BoundField(name='title', type=<class 'str'>, default=Unset, default_factory=None, optional=False)>

Iterating over set fields only
------------------------------

Models provide built-in iterator that can be used to iterate over fields that
are set:

.. doctest::

    >>> book = Book(author="John Doe", title="My Book")
    >>> list(book)
    ['title', 'author']

The iterator iterates over fields in their declaration order and skips ones
that are not set.

Comparing models
----------------

Models can be compared. Models ``a`` and ``b`` are equal if and only if:

* both ``a`` and ``b`` are instances of same model class,
* both ``a`` and ``b`` have same fields set,
* for each field set in ``a``, corresponding field in ``b`` has exactly the
  same value.

For example:

.. doctest::

    >>> Book() == Bookstore()
    False
    >>> Book(author="John Doe", year=2024) == Book(year=2024)
    False
    >>> Book(author="John Doe", year=2024) == Book(author="Jane Doe", year=2024)
    False
    >>> Book(author="John Doe", year=2024) == Book(author="John Doe", year=2024)
    True

Validating models
-----------------

Modelity does not run validation on its own when models are created or
modified. This is one of core functionalities, dictated by the fact that
Modelity cannot determine at what time point the model should be considered
valid. In other words, since Modelity provides mutable models with fields that
can either be initialized via constructor, or set later, it is not possible to
determine whether lack of fields in constructor is a mistake, or intentional
action. Making validation completely separate from data parsing solves this
problem at the cost of requiring the user to call
:meth:`modelity.model.Model.validate` manually.

Okay, so let's now check how this works. Let's assume that ``Book`` model is
used to validate some data input form, where application user can create book
records. Initially, the application will show empty form, as the user did not
enter any values yet. Therefore, initially the ``Book`` model should be created
without arguments:

.. doctest::

    >>> book = Book()
    >>> book
    Book(title=Unset, author=Unset, publisher=Unset, year=Unset)

Let's now assume, that each field is bound with corresponding form field and is
set with whatever is entered by the user. For example, the user has entered
book title and author, modifying the model in similar way as presented below:

.. doctest::

    >>> book.title = "The Life of John Doe"
    >>> book.author = "John Doe"
    >>> book
    Book(title='The Life of John Doe', author='John Doe', publisher=Unset, year=Unset)

And now comes the part where separation of concerns brings a value - the form
contains *Add* button used to add book to the application's database. This is
the part where **validation** should take place, as we require only valid books
to be accepted:

.. doctest::

    >>> book.validate()
    Traceback (most recent call last):
        ...
    modelity.exc.ValidationError: validation of model 'Book' failed with 2 error(-s):
      publisher:
        modelity.RequiredMissing {}
      year:
        modelity.RequiredMissing {}

Now, thanks to the :exc:`modelity.exc.ValidationError` exception being raised,
the user will be informed that the form is still missing 2 required fields:
``publisher`` and ``year``. And now, after filling in missing data, the model
becomes valid and can be further processed by the application:

.. doctest::

    >>> book.publisher = "XYZ"
    >>> book.year = 2024
    >>> book.validate()

Dumping models to ``dict`` objects
----------------------------------

Models can be converted to dictionaries, where each key represents a field, and
each value - value for that field. This is mostly useful for converting models
into objects that can later be encoded to some textual or binary format, to
JSON for instance. Modelity does not provide JSON encoder by its own (there are
several available out there) but it can generate basically any dict thanks to
advanced built-in filtering and parsing customization.

Let's once again take a look at previously declared ``Book`` model and run
:meth:`modelity.model.Model.dump` for it to see what will be the results:

.. doctest::

    >>> book = Book()
    >>> book.dump()
    {'title': Unset, 'author': Unset, 'publisher': Unset, 'year': Unset}
    >>> book.year = "2024"
    >>> book.dump()
    {'title': Unset, 'author': Unset, 'publisher': Unset, 'year': 2024}

By default, Modelity dumps all fields, even unset ones, and outputs same values
as you would get by reading attributes directly. This default behavior can be
changed by applying custom filtering function implementing
:class:`modelity.interface.IDumpFilter` protocol. For instance, it is fairly
easy to get rid of unset fields:

.. doctest::

    >>> book = Book(year=2024)
    >>> book.dump(lambda v, l: (v, True) if v is Unset else (v, False))
    {'year': 2024}

Check the documentation of the :class:`modelity.interface.IDumpFilter` protocol
to read more about how to create custom filters.
