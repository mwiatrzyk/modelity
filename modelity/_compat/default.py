from typing import Any, Mapping

from modelity import _export_list

__all__ = export = _export_list.ExportList()  # type: ignore


@export
def get_annotations_from_class_attrs(attrs: Mapping) -> Mapping:
    return attrs.get("__annotations__", {})
