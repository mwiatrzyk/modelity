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

