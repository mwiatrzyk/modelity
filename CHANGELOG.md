## 0.16.0 (2025-07-12)

### BREAKING CHANGES

- replace `FieldInfo`'s `optional` with `modelity.types.StrictOptional[T]` type
- Methods for iterating through hooks were dropped from
the public interface of the `ModelMeta` class and made private. These
kind of method are very unlikely to be used unless someone wishes to
implement `Model` base class from scratch.
- hide `make_type_descriptor` from public interface

### Feat

- add `field_info` helper for creating `FieldInfo` objects in a linter-satisfying way
- replace `FieldInfo`'s `optional` with `modelity.types.StrictOptional[T]` type
- field is optional if it has default value set
- split hook interfaces between model-scoped and field-scoped hooks
- hide `make_type_descriptor` from public interface

## 0.15.0 (2025-07-05)

### BREAKING CHANGES

- postprocessors can now access/set other fields

### Feat

- postprocessors can now access/set other fields

## 0.14.0 (2025-07-05)

### Feat

- add `modelity.model.type_descriptor_factory` decorator for registering 3rd party types

## 0.13.0 (2025-05-07)

### BREAKING CHANGES

- add separate `UNION_PARSING_ERROR` and handle union parsing errors with single, dedicated error
- Error code cleanup has been made to reduce the total
number of built-in error codes and make it more parametric.

### Feat

- add separate `UNION_PARSING_ERROR` and handle union parsing errors with single, dedicated error

## 0.12.0 (2025-05-04)

### BREAKING CHANGES

- Attribute `__model_prevalidators__` was removed from
`ModelMeta`.
- Attribute `__model_postvalidators__` was removed from
`ModelMeta`.
- Attribute `__model_field_validators__` was removed from
`ModelMeta`.
- Attribute `__model_field_preprocessors__` was removed from
`ModelMeta`.
- Attribute `__model_field_postprocessors__` was removed from
`ModelMeta`.

## 0.11.0 (2025-05-04)

### BREAKING CHANGES

- Previously, the Model had `__loc__` property that was
set when model was assigned to a field in a parent model. Now, this
behavior was dropped and full location will only be used if the model is
initialized or validated. Modifying fields will not show absolute
location when error is reporteds, just the location of the fragment that
was modified. Now it should be possible to reuse same model instance in
two different models if needed.
- When declaring custom type, then
`__modelity_type_descriptor__` function then it can use any subsequence
of these arguments: `typ`, `make_type_descriptor` and `type_opts`. For
example.

### Feat

- remove `__loc__` from Model and container types

## 0.10.0 (2025-05-01)

### BREAKING CHANGES

- rename `modelity.interface.IConstraintCallable` into `modelity.interface.IConstraint`
- sentinel rename: `modelity.interface.EXCLUDE` -> `modelity.interface.DISCARD`

### Fix

- add missing calls to `filter` when serializing models

### Feat

- add support for fields of type `ipaddress.IPv4Address`
- add `modelity.mixins` module providing general purpose mixin classes to reduce boilerplate code
- add support for `ipaddress.IPv6Address` type
- add and use `modelity.mixins.ExactDumpMixin` mixin that adds `dump` method returning value unchanged

## 0.9.0 (2025-04-27)

### BREAKING CHANGES

- Modelity is now using completely redesigned built-in
type system made using ITypeDescriptor protocol, that glues together
methods for parsing, serializing and validating values of a given type.
The change also included some breaking changes in the Modelity API.

### Fix

- update README and add missing release info

## 0.8.0 (2025-04-27)

### Feat

- custom types can now be easily registered by defining `__modelity_type_descriptor__` static function returning type descriptor

## 0.7.0 (2024-11-14)

### BREAKING CHANGES

- type parser factories now receive `model_config` instead of `provider`
- add `config` argument to parsers, processors and validators to render human-readable error messages
- use `IError` and `IInvalid` protocols in interface to get rid of dependency towards errors module

### Feat

- type parser factories now receive `model_config` instead of `provider`
- add `config` argument to parsers, processors and validators to render human-readable error messages
- use `IError` and `IInvalid` protocols in interface to get rid of dependency towards errors module

## 0.6.0 (2024-10-29)

### Feat

- add `ModelError` as a common base class for `ParsingError` and `ValidationError`

## 0.5.0 (2024-10-28)

### Fix

- when dumping, allow subclasses of `str` and `bytes` to avoid unwanted recursion

### Feat

- allow `str` field to be initialized with `bytes` and vice-versa

## 0.4.0 (2024-10-27)

### BREAKING CHANGES

- rename `create_valid` to `load_valid` for compatibility with `load` method
- refactor constraints module and get rid of `Range` constraint in favor of jsut `MinValue` and `MaxValue`

### Feat

- add `default_factory` option to `Field` class
- rename `create_valid` to `load_valid` for compatibility with `load` method
- add `MinLength` and `MaxLength` constraints
- re-run constraint checks for fields with constraints defined while validating

## 0.3.0 (2024-10-21)

### Feat

- add `Model.get_value` method allowing to perform full model lookup to find a value by its absolute location

## 0.2.0 (2024-10-21)

### BREAKING CHANGES

- It is now required to explicitly pass `loc` when
returning `Error` objects from the validator directly. However, this
change makes the whole validator work in more explicit way, and allows
generating errors also for other fields if needed.
- Now it is required to explicitly pass `loc` when
`Error` object is returned from the validator.

### Feat

- add support for `loc` argument to functions decorated with `field_validator` decorator
- add support for `loc` argument for functions decorated with `model_validator`

## 0.1.0 (2024-10-20)

### BREAKING CHANGES

- rename `root_model` to `root` in user defined validators
- reorder `value` and `loc` args in `IDumpFilter` protocol
- `model_validator` now allows modifying `errors` list instead of just reading it
- exchange the order of `errors` and `root` args of `model_validator`
- add `pre` option to `model_validator`, allowing it to optionally be called before any other validators

### Feat

- add support for `root_model` argument in `field_validator` decorator
- rename `root_model` to `root` in user defined validators
- reorder `value` and `loc` args in `IDumpFilter` protocol
- `model_validator` now allows modifying `errors` list instead of just reading it
- exchange the order of `errors` and `root` args of `model_validator`
- add `pre` option to `model_validator`, allowing it to optionally be called before any other validators

## 0.0.3 (2024-10-20)

### Fix

- create initial README content and add classifiers and tags

## 0.0.2 (2024-10-20)

### Fix

- add missing MIT license file

## 0.0.1 (2024-10-20)

Initial release.

