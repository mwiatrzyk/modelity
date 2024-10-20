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

