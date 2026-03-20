![PyPI - Version](https://img.shields.io/pypi/v/modelity)
![PyPI - Downloads](https://img.shields.io/pypi/dm/modelity)
![PyPI - License](https://img.shields.io/pypi/l/modelity)

# Modelity

Modelity is a domain-oriented validation engine for structured Python models.

It separates construction from validation, treats models as trees, and provides
location-aware structured errors.

Modelity is designed for complex domain models — not just data containers.

## Installation

```shell
pip install modelity
```

## Core idea

Modelity enforces a clear lifecycle:

```
raw input
   ↓
parsing (field-level normalization)
   ↓
fixup (user-defined post-initialization or post-modification hooks)
   ↓
model instance
   ↓
validation (domain invariants)
   ↓
fully validated model
```

A model can exist in *parsed but not yet validated* state.

## Features

* Declare models using type annotations just like Python dataclasses.

* Clean separation of concerns:
    - **parsing** is executed on raw data when model is created or modified,
    - **fixup** runs after successful parsing and only for explicitly defined
      `model_fixup` or `field_fixup` hooks,
    - **validation** is executed on demand on successfully parsed model instances.

* Error handling done via dedicated `Error` class allowing to set error
  location, failed value, error code, code-specific error data and few more.

* Support for unset fields via dedicated `Unset` sentinel.

* Support for typed mutable containers (lists, sets and dicts) with type
  checking and parsing on modifications.

* Support for user-defined hooks for **parsing**, **fixup** and **validation**
  stages.

* Ability to access any part of the model from any user-defined validation hook
  to achieve complex cross-field validation logic.

* Ability to access custom **validation context object** from any user-defined
  validation hook for even more complex validation strategies (like having
  different validators when model is created, when model is updated or when
  model is fetched over the API).

* Ability to register custom types for **parsing** stage.

## Lifecycle overview

1. Class build time (meta phase)

    * Inheritance handling (i.e. collecting fields and hooks from base and
      mixin classes)
    * Recursive type annotation analyzer and compiler (i.e. constructs **type
      parser** for each type and caches in the model class)
    * Configuration of user-defined hooks (i.e. precomputing and assigning to
      fields)

2. Parsing stage (construction-time)

    Triggered on:
    * model instantiation,
    * attribute assignment,
    * mutable container modification.

    Pipeline:
    * raw value (i.e. input value)
    * field preprocessing chain
    * field type verification and parsing
    * field postprocessing chain
    * model value (i.e. target value)

    Parsing runs independently for each model field (or typed mutable container
    element) and is executed when new model object is created, when existing
    model is modified, or when typed mutable container is modified.

    Errors accumulate and raise `ParsingError`.

3. Fixup stage (construction-time or explicit)

    Triggered:
    * on model instantiation
    * on attribute assignment (only `field_fixup` hooks)
    * via `fixup` helper

    This stage allows to use user-defined model-level or field-level hooks to
    fill in the model object with missing or derived data. This is similar to
    ``__post_init__`` method of Python dataclasses, but slightly more capable.

3. Validation stage (explicit)

    Triggered via:

    ```python
    from modelity.api import validate

    validate(model)
    ```

    Pipeline:
    * unverified model instance (i.e. the input model from parsing stage)
    * model prevalidation chain
    * field validation chain (runs for each set field)
    * location validator chain (runs for matched model locations only)
    * model postvalidation chain
    * verified model instance

    Errors accumulate and raise `ValidationError`.

## Design principles

**Separation of concerns**

* **Parsing** is about structure.
* **Validation** is about meaning.

**Deterministic execution order**

* Both parsing and validation stages have a fixed and predictable order of steps.
* User-defined hooks are always executed in their declaration order.

**Tree-aware architecture**

* Models are treated as trees, not flat structures.
* Location of the value in the model is given by absolute path pointing to a
  tree leaf where the value is stored.
* Validation and serialization is implemented using visitors.

**First-class location object**

Modelity is using special `Loc` class for encoding locations in the model. This
is tuple-like type with some addons.

**Structured error model**

Errors are first-class objects with following properties:
* **location** in the model (using the `Loc` type),
* error **code** (supporting both built-in error codes and custom ones),
* error **message** (human-readable),
* incorrect **value**
* code-specific **metadata** (e.g. failed regex pattern, expected field length
  range, supported types etc.)

**Minimum external dependencies**

Modelity currently only depends on `typing-extensions` package which is needed
for some additional typing primitives and for dataclass-like UX.

**Pure Python implementation**

Modelity is currently implemented in pure Python by design to make it easily
portable between Python versions and alternative Python interpreters.

## When to use Modelity

Modelity is well suited for:
* complex domain models
* nested and repeated structures
* cross-field invariants
* structured API validation
* systems requiring deterministic validation behavior

## When not to use Modelity

Modelity may be unnecessary for:
* simple DTO containers
* lightweight data coercion
* cases where parsing alone is sufficient

## Example

### Definition of domain models

```Python
from modelity.api import (
    Model,
    Gt,
    UserError,
    ValidationError,
    fixup,
    validate,
    field_fixup,
    model_fixup,
    field_validator,
    field_postprocessor
)


class OrderItem(Model):
    name: str
    quantity: Annotated[int, Gt(0)]
    price: Annotated[float, Gt(0)]

    # -- field-scoped postprocessing

    @field_postprocessor("name")
    def _strip(cls, value: str):
        return value.strip()

    @property
    def total_price(self) -> float:
        return self.quantity * self.price


class Order(Model):
    items: list[OrderItem]
    total: Optional[float] = None
    modified: Optional[datetime.datetime] = None
    created: Optional[datetime.datetime] = None

    # -- construction or modification fixup hooks

    @field_fixup("items")
    def _update_total(self):
        self.total = sum(x.total_price for x in self.items)

    # -- construction fixup hooks

    @model_fixup()
    def _update_timestamps(self):
        now = datetime.datetime.now()
        self.modified = now
        if self.created is None:
            self.created = now

    # -- validation hooks

    @field_validator("total")
    def _verify_total(self):
        if self.total != sum(x.total_price for x in self.items):
            raise UserError(msg="incorrect total price", code="PRICE_CHECK_ERROR")
```

### Creating model instances

```Python
order = Order(items=[
    OrderItem(name="apple", quantity=2, price=3.0),
    OrderItem(name="banana", quantity="1", price=2.0),  # "1" will automatically be converted to 1
])

print(order.total)  # Would print: 8.0; it was automatically computed by fixup hook
```

### Altering model instances

Modelity models are **mutable** by default and altering fields after model
creation results in same parsing mechanics being used:

```Python
order.items.append(OrderItem(name="orange", quantity=1, price=1))
order.total = "10.0"  # Will be converted to 10.0 float; but this is not the right value
```

### Fixing up model instances

After alteration it is recommended (although not required) to run `fixup`
helper to ensure that all fixup hooks are called with updated data:

```Python
from modelity.api import fixup

print(order.total)  # Would print: 10.0

fixup(order)  # Will fix total total price

print(order.total)  # Would print: 9.0;
```

### Validating models

At this step `order` object is in successfully parsed (i.e. all fields have the
right types), but not yet validated state. To validate it against built-in and
user-defined constraints you have to explicitly call `validate` function:

```Python
from modelity.api import validate

validate(order)

print("The order is valid")
```

### Serializing models

Modelity serialization mechanism does not produce JSON or other formats, but
encodes model data into JSON-compatible dict that can later be encoded using
other libraries:

```Python
from pprint import pprint

from modelity.api import dump

order_dict = dump(order)

pprint(order_dict)  # Will print order object encoded to dict
```

### Deserializing models

Serialized data can be back decoded into model instance. Deserialization
involves parsing, fixup and validation stages automatically:

```Python
from modelity.api import load

order = load(Order, order_dict)

print(order.total)  # Would print: 9.0
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
