import annotationlib  # type: ignore

from typing import Any, Mapping

from modelity import _export_list

__all__ = export = _export_list.ExportList()  # type: ignore


@export
def get_annotations_from_class_attrs(attrs: Mapping) -> Mapping:
    annotate = annotationlib.get_annotate_from_class_namespace(attrs)
    if annotate is None:
        return {}
    return annotationlib.call_annotate_function(annotate, format=annotationlib.Format.FORWARDREF)
