import datetime
from typing import Optional

from modelity.model import Model, FieldInfo, field_postprocessor
from modelity.unset import Unset


class TestFieldPostprocessor:

    class TestPostprocessorCanSetOtherFields:
        class Dummy(Model):
            modified: Optional[datetime.datetime] = None
            created: Optional[datetime.datetime] = FieldInfo(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))  # type: ignore

            @field_postprocessor("created")
            def _postprocess_created(self, value):
                if self.modified is Unset or self.modified is None:
                    self.modified = value
                return value

        def test_created_model_has_both_created_and_modify_equal(self):
            dummy = self.Dummy()
            assert dummy.created is not None
            assert datetime.datetime.now(datetime.timezone.utc) >= dummy.created
            assert dummy.created == dummy.modified

        def test_created_model_has_both_created_and_modify_equal_if_only_created_is_given(self):
            dummy = self.Dummy(created=datetime.datetime(1999, 1, 1))
            assert dummy.created is not None
            assert dummy.created == dummy.modified

        def test_model_has_both_fields_different_if_both_fields_are_set_with_two_different_values(self):
            dummy = self.Dummy(created=datetime.datetime(1999, 1, 1), modified=datetime.datetime(1999, 1, 2))
            assert dummy.created != dummy.modified
