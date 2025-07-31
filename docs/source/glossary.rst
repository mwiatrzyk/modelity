Glossary
========

.. glossary::

    Type descriptors
        Modelity built-in mechanism for handling type parsing and value
        visiting logic.

        It is provided by :class:`modelity.interface.ITypeDescriptor` base
        class. Modelity evaluates type descriptors when model type is created,
        and later operates on closures created during model construction.
        Thanks to this approach the logic behind type support is quite simple,
        without degrading runtime performance too much.

        Type descriptors can be built-in for the types Modelity supports, with
        a possibility to register custom types or 3rd party types if needed.

    Data model
        A subclass of :class:`modelity.model.Model` class with data-specific
        fields and their types provided via type annotations like in
        :mod:`dataclasses` module.

    Data parsing
        First stage of data processing performed by Modelity when
        :term:`data model<Data model>` is either instantiated or modified. This
        stage, executed independently for each model field, guarantees that the
        right type was used for each field. If the value cannot be parsed to
        the right type, then :exc:`modelity.exc.ParsingError` is raised.

    Model validation stage
        Second stage of data processing, performed on demand by call to
        :func:`modelity.model.validate` function on an initialized model
        object.

        Validation stage, as executed after :term:`data parsing<Data parsing>`
        stage, can assume that all fields are either :term:`unset`, or set to a
        value of the right type. During validation, validators can access
        entire model to perform complex cross-field checks.

    Unset field
        Field that does not have value assigned.

        Each unset field is set to the :obj:`modelity.unset.Unset` object,
        which is a singleton instance of the :class:`modelity.unset.UnsetType`
        class. Following scenarios result in a field being unset:

        * field is omitted in the model's constructor and have no default value provided,
        * field was deleted from a model, for example by calling ``del model.attr``
        * field was explicitly set to :obj:`modelity.unset.Unset` object.

    Preprocessors
        User-defined :term:`data parsing<Data parsing>` stage hooks for
        filtering input data **before** the data is passed further to the type
        parsers. Preprocessors can be defined for models by using
        :func:`modelity.model.field_preprocessor` decorator.

        Preprocessors can be used, for example, to strip input data from white
        characters before that data is passed.

        Since preprocessors are part of data parsing stage, each is executed
        independently for each matching field.

    Postprocessors
        User-defined :term:`data parsing<Data parsing>` stage hooks for adding
        custom field-level constraints or filters on values that were already
        converted to a right type. Postprocessors can be declared using
        :func:`modelity.model.field_postprocessor` decorator.
