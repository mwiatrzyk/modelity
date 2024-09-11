from typing import Protocol


class IValidatable(Protocol):
    """Interface that all models implement."""

    def validate(self):
        """Validate this model.

        On success, this method normally returns, meaning that model is valid.

        On failure, this method raises :exc:`modelity.exc.ValidationError`
        containing all errors that caused model validation to fail.

        This method is stateless and it does not affect model's state, therefore
        it can be called several times. It is completely up to the user if,
        when, and how many times this method must be called.
        """
