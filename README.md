# modelity

Data parsing and validation library for Python.

## About

Modelity is a data parsing and validation library allowing to declare mutable
data models using Python's type hinting mechanism. Modelity design was based on
following assumptions:

* Use of recursive **type parser providers**, allowing to create parsers for
  both built-in types, and user-defined ones.

* Use of cache mechanism, so type parser created once can be reused by other
  models, or other fields.

* Clean separation between **data parsing** and **model validation** steps,
  with automatic data parsing whenever model is created or modified, and
  validation phase being executed on user's demand.

* Separation between model-scoped validators (executed always) and field-scoped
  validators (executed for selected fields and only if the field has value
  set).

* Ability to inspect entire model when validating it, even from a nested model.

* Use of separate ``Unset`` type to differentiate between fields set to
  ``None`` and fields that are unset.

* Easily customized with user-defined parsing and/or validation hooks provided
  by decorators.

* Models are mutable, so modifying a field after model is created, appending a
  value to typed list field etc. invokes parsing mechanism, keeping integrity
  of the entire model.

## Rationale

Why I have created this toolkit?

Well, for fun, that's for sure :-)

I also wanted to resurrect some ideas from my over 10-year old and abandoned
project Formify (which you can still find on my GH profile), as it was already
supplied with data parsing and validation separation mechanism. Unfortunately,
the name Formify was already in use (as I have never released it), so I've
decided to go with a completely new project name.

And last but not least - the separation of concerns (**parsing** and
**validation**) is the feature that I needed in several projects, both private
and commercial, and that I did not find in any toolkit I've been using, forcing
me to subclassing and/or creating separate project-specific tools to make
validation being separate from data parsing. I needed this especially for large
models, with lots of nested submodels, that could not be easily validated
without being able to inspect entire model tree (f.e. when validity of nested
model depends on a value of particular parent model field).

## Usage

I will create a separate guide in the future, but for now please check out the
examples directly in the source code:

https://github.com/mwiatrzyk/modelity/tree/main/tests/examples

## License

This project is released under the terms of the MIT license.

## Author

Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
