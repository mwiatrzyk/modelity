Advanced user's guide
=====================

Advanced validation patterns
----------------------------

Accessing entire model tree from nested model's validator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Modelity, it is possible to perform nested model validation that depends
on some properties defined in the parent model, or in another nested model.
For example, we can have the list of forbidden logins declared in the root
model, and a validator in child model that checks if the login is forbidden
or not:

.. testcode::

    from modelity.model import Model
    from modelity.helpers import validate
    from modelity.hooks import field_validator

    class User(Model):
        login: str

        @field_validator('login')
        def _validate_login(root, value):  # root - validated model, value - current login
            if isinstance(root, UserStore):  # execute only when User is part of UserStore
                if value in root.logins_forbidden:
                    raise ValueError(f'the login is forbidden: {value}')

    class UserStore(Model):
        logins_forbidden: list[str]
        users: list[User]

.. doctest::

    >>> store = UserStore(logins_forbidden=['foo'], users=[])
    >>> store.users.append(User(login='spam'))  # OK
    >>> store.users.append(User(login='foo'))  # will not fail here, but login is forbidden
    >>> validate(store)  # 'store' is the root model for validators
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'UserStore' failed with 1 error(-s):
      users.1.login:
        the login is forbidden: foo [code=modelity.EXCEPTION, data={'exc_type': <class 'ValueError'>}]

Why not validating such or similar cases inside **UserStore** object?

Well, that depends on what kind of errors you want to receive. In the
example above, the error is related to the **User** model, therefore it
will be duplicated if more such objects are added to the list, producing a more
verbose error report:

.. doctest::

    >>> store.logins_forbidden.append('bar')
    >>> store.users.append(User(login='bar'))  # 'bar' is also forbidden
    >>> validate(store)
    Traceback (most recent call last):
      ...
    modelity.exc.ValidationError: validation of model 'UserStore' failed with 2 error(-s):
      users.1.login:
        the login is forbidden: foo [code=modelity.EXCEPTION, data={'exc_type': <class 'ValueError'>}]
      users.2.login:
        the login is forbidden: bar [code=modelity.EXCEPTION, data={'exc_type': <class 'ValueError'>}]

If you need single combined error, then it would be better to validate
inside **UserStore** instead.

.. important::

    Choose carefully when to validate inside child model, and when to
    validate inside parent model. Although both have their pros and cons,
    accessing parent model from a child model provides direct dependency
    towards parent model.
