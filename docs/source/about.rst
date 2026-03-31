About
=====

What is Modelity?
-----------------

Modelity is a domain-oriented validation engine for structured Python models.

It separates construction from validation, treats models as trees, provides
rich set of hooks and location-aware structured errors.

Modelity is designed for complex domain models -- not just data containers.

Core idea
---------

Modelity enforces a clear lifecycle::

    raw input
       ↓
    parsing (field-level normalization)
       ↓
    model instance
       ↓
    validation (domain invariants)
       ↓
    fully validated model

A model can exist in **parsed but not yet validated** state. Moreover, it can
be modified at any time and revalidated again if needed.

Features
--------

* Declaring models using type annotations in similar way as when using Python's
  built-in :mod:`dataclasses` module.
* Explicit handling of unset fields via dedicated :obj:`modelity.api.Unset`
  sentinel
* Data flow is split into 2 stages:
    - **parsing** (executed when model object is constructed or modified)
    - **validation** (executed on demand)
* Easily customizable with hooks (see :mod:`modelity.hooks` for more details)
* Each validator can access **entire model tree**
* Each validator can access user-defined **context object** and perform
  validation against dynamic data that is not directly available in models
  (e.g. data fetched from API)
* Structured error reporting as a list of :class:`modelity.api.Error` objects.
* Use of predefined error codes instead of error messages for easier
  customization of error reporting
* Ease of providing custom types with :func:`modelity.api.register_type_handler_factory` function

Design principles
-----------------

**Use of type annotations to declare model fields**

Creating model in Modelity is as easy as creating a dataclass and if you know
dataclasses, then you already know how to create models using Modelity:

.. testcode::

    from modelity.api import Model

    class User(Model):
        name: str
        email: str
        age: int

**Separation of concerns**

* Parsing and fixup is about structure.
* Validation is about meaning.

**Tree-aware architecture**

* A model is a tree, with fields being its leafs.
* If a field is a nested model, then such field becomes a node and nested model's
  fields become leafs.
* If a field is a container (e.g. list) then the container becomes a node, and
  its items become leafs.
* Each value has a **unique location** in the model.

**Use of visitor pattern**

Since models are trees and each value has a unique location it would be good to
have a one common mechanism of walking through entire model tree. This is done
with **visitors** that are used to:

* run fixup hooks,
* run validation hooks,
* execute model serialization.

Modelity also provides a :class:`modelity.api.ModelVisitor` base class to
create custom visitors if needed.

**Structured error model**

* Single error object is an instance of :class:`modelity.api.Error` class.
* Errors can be reported by adding error objects to ``errors`` list that can be
  accessed from user-defined hooks.
* Errors reported during **parsing stage** are collected and raised as
  :exc:`modelity.api.ParsingError`
* Errors reported during **validation stage** are collected and raised as
  :exc:`modelity.api.ValidationError`

**Explicit unset field handling**

Modelity uses a :obj:`modelity.api.Unset` sentinel as a default value for unset
fields and differentiates between field being **unset** and field being set to
``None``.

**Minimum external dependencies**

Modelity only depends on :mod:`typing_extensions` package and only to backport
things that are missing in :mod:`typing` module.

**Pure Python implementation**

Modelity is currently implemented in pure Python by design to make it easily
portable between Python versions and alternative Python interpreters.

When to use Modelity
--------------------

Modelity is well suited for:

* complex domain models
* cross-field invariants
* structured API validation
* applications where models are fed in progressively and validated after data
  filling ends (e.g. web forms, GUIs)
* systems requiring deterministic validation behavior
* systems where validation strategy depends on some external factors
  (validation context), not solely on model declarations
* systems that use error codes to later return the right error message for the
  user

When not to use Modelity
------------------------

Modelity may be unnecessary for:

* simple DTO containers
* lightweight data coercion
* cases where parsing alone is sufficient

A brief history
---------------

Why I have created this library?

First reason is that I didn't find such clean separation in known data parsing
tools, and found myself needing such freedom in several projects - both
private, and commercial ones. Separation between parsing and validation steps
simplifies validators, as validators in models can assume that they are called
when model is instantiated, therefore they can access all model's fields
without any extra checks.

Second reason is that I often found myself writing validation logic from the
scratch for various reasons, especially for large models with lots of
dependencies. Each time I had to validate some complex logic manually I was
asking myself, why don't merge all these ideas and make a library that already
has these kind of helpers? For example, I sometimes needed to access parent model
when validating field that itself is another, nested model. With Modelity this
became extremely easy as the root model (one that is validated) can
automatically be referenced from any user-defined validator no matter if it is
defined in the root model, or in the nested model.

Third reason is that I wanted to finish my over 10 years old, abandoned project
Formify (the name is already in use, so I have chosen new name for new project)
which I was developing in free time at the beginning of my professional work.
That project was originally made to handle form parsing and validation to be
used along with web framework. Although the project was never finished, I've
resurrected some ideas from it, especially parsing and validation separation.

And last, but not least... I made this project for fun with a hope that maybe
someone will find it useful :-)
