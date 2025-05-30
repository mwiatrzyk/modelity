Introduction
============

About
-----

Modelity is a data parsing and validation library, written purely in Python,
and based on the idea that data parsing and validation should be separated from
each other, but being a part of single toolkit for ease of use.

In Modelity, data parsing is executed automatically once data model is
instantiated or modified, while validation needs to be explicitly called by
client code, when collecting data to initialize model with is done. Thanks to
this approach, models can be feed with data progressively (f.e. in response to
user's input), while still being able to validate at any time.

Features
--------

* Declare models using type annotations
* Uses **slots**, not **descriptors**, making reading from a model as fast as
  possible
* Clean separation between automatic **data parsing** (executed when model is
  created or modified) and **model validation** (executed on demand)
* Clean differentiation between **unset** fields (via special
  :class:`modelity.unset.UnsetType` type) and optional fields set to ``None``
* Easily customizable via **pre-** and **postprocessors** (executed during data
  parsing), **model-level validators**, and **field-level validators** (both
  executed during model validation)
* Ability do access any field via **root model** (the one for each validation
  is executed) from any custom validator, allowing to implement complex
  cross-field validation logic
* Ability to add custom validation context for even more complex validation
  strategies.
* Use of predefined error codes instead of error messages for easier
  customization of error reporting
* Ease of providing custom types simply by defining
  ``__modelity_type_descriptor__`` static method in user-defined type.

Rationale
---------

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
when validating field that itself is another, nested model. With Modelity, it
is possible, as root model (the one that is validated) is populated to all
nested models recursively.

Third reason is that I wanted to finish my over 10 years old, abandoned project
Formify (the name is already in use, so I have chosen new name for new project)
which I was developing in free time at the beginning of my professional work.
That project was originally made to handle form parsing and validation to be
used along with web framework. Although the project was never finished, I've
resurrected some ideas from it, especially parsing and validation separation.
You can still find source code on my GH profile.

And last, but not least... I made this project for fun with a hope that maybe
someone will find it useful :-)
