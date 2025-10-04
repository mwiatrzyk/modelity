# modelity

Data parsing and validation library for Python.

## About

Modelity is a data parsing and validation library, written purely in Python,
and based on the idea that data parsing and validation should be separated from
each other, but being a part of single toolkit for ease of use.

In Modelity, **data parsing** is executed **automatically** once data model is
**instantiated or modified**, while model **validation** needs to be explicitly
called by the user. Thanks to this approach, models can be feed with data
progressively (f.e. in response to user’s input), while still being able to
validate at any time (f.e. in reaction to button click).

## Features

* Declare models using type annotations
* Uses slots, not descriptors, making reading from a model as fast as possible
* Clean separation between **data parsing** stage (executed when model is
  created or modified) and **model validation** stage (executed on demand)
* Clean differentiation between unset fields (via special `Unset` sentinel) and
  optional fields set to `None`
* Easily customizable via pre- and postprocessors (executed during data
  parsing), model-level validators, and field-level validators (both executed
  during model validation)
* Ability do access any field via **root model** (the one for each validation is
  executed) from any custom validator, allowing to implement complex
  cross-field validation logic
* Ability to add custom **validation context** for even more complex validation
  strategies (like having different validators when model is created, when
  model is updated or when model is fetched over the API).
* Use of predefined error codes instead of error messages for easier
  customization of error reporting if needed
* Ease of providing custom types simply by defining
  `__modelity_type_descriptor__` static method in user-defined type, or by
  using `type_descriptor_factory` hook for registering 3rd party types.

## Rationale

Why I have created this library?

First reason is that I didn’t find such clean separation in known data parsing
tools, and found myself needing such freedom in several projects - both
private, and commercial ones. Separation between parsing and validation steps
simplifies validators, as validators in models can assume that they are called
when model is successfully instantiated, with all fields parsed to their
allowed types, therefore they can access all model’s fields without any extra
checks.

Second reason is that I often found myself writing validation logic from the
scratch for various reasons, especially for large models with lots of
dependencies. Each time I had to validate some complex logic manually I was
asking myself, why don’t merge all these ideas and make a library that already
has these kind of helpers? For example, I sometimes needed to access parent
model when validating field that itself is another, nested model. With
Modelity, it is easy, as root model (the one that is validated) is
populated to all nested models' validators recursively.

Third reason is that I wanted to finish my over 10 years old, abandoned project
**Formify** (the name is already in use, so I have chosen new name for new
project) which I was developing in free time at the beginning of my
professional work as a Python developer. That project was originally made to
handle form parsing and validation to be used along with web framework.
Although the project was never finished, I’ve resurrected some ideas from it,
especially parsing and validation separation. You can still find source code on
my GitHub profile: https://github.com/mwiatrzyk.

And last but not least, I don’t intend to compete with any of the existing
alternatives — and there are plenty of them. I simply created this project for
fun and decided to release it once it became reasonably usable, hoping that
maybe someone else will find it helpful.😊

## Example

Here's a condensed example of how to use Modelity:

```python
import json
import datetime
import typing

from modelity.api import Model, ValidationError, ModelError, validate, dump, load

# 1. Define models

class Address(Model):
    address_line1: str
    address_line2: typing.Optional[str]
    city: str
    state_province: typing.Optional[str]
    postal_code: str
    country_code: str

class Person(Model):
    name: str
    second_name: typing.Optional[str]
    surname: str
    dob: datetime.date
    address: Address


# 2. Create instances (parsing runs automatically)

addr = Address(
    address_line1="221B Baker Street",
    address_line2=None,
    city="London",
    state_province=None,
    postal_code="NW1 6XE",
    country_code="GB"
)

person = Person(
    name="Sherlock",
    second_name=None,
    surname="Holmes",
    dob=datetime.date(1854, 1, 6),
    address=addr
)

#: 3. Validate instances (on demand)

try:
    validate(person)
except ValidationError as e:
    print("Model is not valid: ", e)
    raise

# 4. Dump to JSON-serializable dict

person_dict = dump(person)
person_json = json.dumps(person_dict)  # Dump to JSON; use any lib you like to do that

# 5. Parse from dict

person_dict = json.loads(person_json)
try:
    same_person = load(Person, person_dict)  # Parsing + validation made by helper
except ModelError as e:  # Base for: ValidationError, ParsingError
    print("Model parsing or validation failed: ", e)
    raise

# 6. Accessing fields (just like using normal dataclasses).

print(same_person.address.country_code)
```

## Documentation

Please visit project's ReadTheDocs site: https://modelity.readthedocs.io/en/latest/.

## Disclaimer

**Modelity** is an independent open-source project for the Python ecosystem. It
is not affiliated with, sponsored by, or endorsed by any company, organization,
or product of the same or similar name. Any similarity in names is purely
coincidental and does not imply any association.

## License

This project is released under the terms of the MIT license.

## Author

Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
