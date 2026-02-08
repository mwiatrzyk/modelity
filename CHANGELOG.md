## 0.33.0 (2026-02-08)

### BREAKING CHANGES

- the method `ErrorFactory.parse_error` now requires `msg` to be passed as keyword arg
- method `ErrorFactory.conversion_error` now accepts optional `reason` as positional or keyword arg and allows to pass custom `msg` and `extra_data`
- adjust `ErrorFactory.invalid_string_format` method interface to comply with other factories
- make all `ErrorFactory` methods to strictly follow positional-only/keyword-only argument rules

### Feat

- the method `ErrorFactory.parse_error` now requires `msg` to be passed as keyword arg
- method `ErrorFactory.conversion_error` now accepts optional `reason` as positional or keyword arg and allows to pass custom `msg` and `extra_data`
- add `**extra_data` to `ErrorFactory.invalid_value` method
- add `msg` and `**extra_data` parameters to `ErrorFactory.invalid_type` method
- add `msg` parameter to `ErrorFactory.out_of_range` method
- add `msg` parameter to `ErrorFactory.invalid_length` method
- adjust `ErrorFactory.invalid_string_format` method interface to comply with other factories
- make all `ErrorFactory` methods to strictly follow positional-only/keyword-only argument rules
- `ErrorFactory.out_of_range` now supports any comparable type

## 0.32.0 (2026-02-07)

### Feat

- addi optional keyword-only `msg` parameter for `ErrorFactory.invalid_value` error factory function

## 0.31.0 (2026-02-07)

### BREAKING CHANGES

- original values are now passed to visitors
- Since now visitors are responsible for converting input
values (in case of serialization visitors) to closest JSON type. This
allows valiation visitors to access original values instead of converted
ones. Also, the `IModelVisitor` interface was slightly modified.
- drop `output_date(time)_format` parameter and renamed `input_date(time)_formats` to `expected_date(time)_formats`
- refactoring of dump visitors
- `DefaultDumpVisitor` was dropped,
`DefaultValidationVisitor` was renamed to `ValidationVisitor`
- remove `ConditionalExcludingModelVisitorProxy` as the functionality was moved to `JsonDumpVisitorProxy`
- visitors were renamed: DefaultDumpVisitor -> DumpVisitor, DefaultValidateVisitor -> ValidationVisitor
- rename `ConditionalExcludingModelVisitorProxy` to `ModelFieldPruningVisitorProxy`

### Feat

- original values are now passed to visitors
- drop `output_date(time)_format` parameter and renamed `input_date(time)_formats` to `expected_date(time)_formats`
- refactoring of dump visitors
- remove `ConditionalExcludingModelVisitorProxy` as the functionality was moved to `JsonDumpVisitorProxy`

## 0.30.0 (2026-02-05)

### Feat

- add `UserError` exception allowing to raise errors from user hooks instead of manually modifying errors list

## 0.29.0 (2026-02-04)

### BREAKING CHANGES

- drop `Field.optional` property and use `Field.is_optional` method instead
- All other field properties were not computed, just the
`optional` one, so I decided to use an `is_optional()` method instead.
Now the class has better interface, especially when there was
`has_default()` method already defined.
- `Optional[T]` now fails validation if Unset
- Previously `Optional[T]` was allowed to be Unset after
validation and that was causing type contract issues, as `Optional[T]`
defacto allowed 3 types (T, None, UnsetType), not 2 types (T, None). Now
it fails validation when not set while still being optional.

### Feat

- drop `Field.optional` property and use `Field.is_optional` method instead
- add `Field.is_required()` method as the opposite for `Field.is_optional()`
- `Optional[T]` now fails validation if Unset

## 0.28.0 (2026-02-01)

### BREAKING CHANGES

- remove hook introspection from the public interface
- error code refactoring of built-in type parsers
- error code refactoring for built-in constraints
- Some of error codes were dropped and replace with new,
more generic ones.

### Feat

- add `modelity.types.LooseOptional` type; an extended optional allowing `Unset` as a valid value
- constraints are now built using dataclasses for __eq__ and __hash__ automation
- add `Range` constraint
- add `LenRange` constraint
- add `ErrorWriter` class for formatting errors and writing to given buffer

## 0.27.0 (2026-01-26)

### BREAKING CHANGES

- remove hook run methods from the public interface
- Removed public logic is now made internal.

### Feat

- add `location_validator` hook for validating values based on location suffix pattern
- drop support for Python 3.9, add support for Python 3.13

## 0.26.0 (2025-10-09)

### Fix

- run `field_validator` for any kind of field

### Feat

- add `visit_model_field_begin` and `visit_model_field_end` methods to `IModelVisitor` interface

## 0.25.0 (2025-10-04)

### Feat

- add built-in support for `YYYY-MM-DD hh:mm:ss ZZZZ` datetime format

## 0.24.0 (2025-09-27)

### Feat

- handle hooks provided by mixin classes

## 0.23.1 (2025-09-14)

### Fix

- `setdefault` method of typed dict now properly parses data
- `update` of typed dict now properly handles multiple parsing errors

## 0.23.0 (2025-09-09)

### Feat

- add support for `pathlib.Path` type

## 0.22.0 (2025-09-08)

### BREAKING CHANGES

- removed `ISupportsValidate` and provided `IValidatableTypeDescriptor` subclass of `ITypeDescriptor` instead
- Dropped generic type support from `ITypeDescriptor`; it
was not necessary, so let's keep things as simple as possible.

### Feat

- removed `ISupportsValidate` and provided `IValidatableTypeDescriptor` subclass of `ITypeDescriptor` instead

## 0.21.0 (2025-09-07)

### Feat

- visitor's `visit_*_begin`-family methods can return True to skip visiting nested items
- `model_prevalidator` hook can return True to skip other validators, both custom and built-in ones

## 0.20.0 (2025-08-25)

### BREAKING CHANGES

- don't assign location to nested models and mutable containers
- remove `IModel` and `IField` from the interface

### Feat

- don't assign location to nested models and mutable containers
- remove `IModel` and `IField` from the interface

## 0.19.0 (2025-08-14)

### Feat

- add `title`, `description` and `examples` fields to `modelity.model.FieldInfo` class

## 0.18.0 (2025-07-28)

### BREAKING CHANGES

- `IFieldPreprocessingHook` was removed from the
interface.
- `IFieldPostprocessingHook` was removed from the
interface.
- `IModelValidationHook` was replaced with
`prevalidate_model` and `postvalidate_model` helpers for running
model-level validation. This allows to run these hooks when implementing
custom validation visitor.
- `IFieldValidationHook` was replaced with
`validate_field` helper for running field-level validation.

### Feat

- refactor hook system

## 0.17.0 (2025-07-27)

### BREAKING CHANGES

- model validation is now made via visitors
- extract decorators from `model` to `hooks` module
- model serialization via `dump` now uses visitors
- rename `BoundField` to `Field`
- `modelity.model.dump` function was moved to `modelity.helpers` module
- the function `modelity.model.validate` was moved to `modelity.helpers`
- all hooks are now imported from `modelity.hooks` module

### Feat

- model validation is now made via visitors
- use absolute locations in mapping, list and set containers
- extract decorators from `model` to `hooks` module
- add `modelity.api` import helper allowing to import public names from all submodules
- add `ModelLoader` helper
- `IConstraint` now inherits from `abc.ABC` and must be used explicitly

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

