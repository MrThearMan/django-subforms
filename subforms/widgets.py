import copy
from typing import Any, Dict, List, Mapping, Optional, Type, Union

from django import forms
from django.http import QueryDict
from django.utils.datastructures import MultiValueDict


__all__ = [
    "DynamicArrayWidget",
    "NestedFormWidget",
]


class DynamicArrayWidget(forms.TextInput):

    template_name = "subforms/array.html"

    class Media:
        js = ["js/subforms.js"]
        css = {"all": ["css/subforms.css"]}

    def __init__(
        self,
        subwidget: Union[Type[forms.Widget], forms.Widget] = forms.TextInput,
        default: Any = "",
        attrs: Optional[Dict[str, Any]] = None,
    ):
        self.subwidget = subwidget() if isinstance(subwidget, type) else copy.deepcopy(subwidget)
        self.default = default
        super().__init__(attrs=attrs)

    def get_context(self, name: str, value: Optional[List[Any]], attrs: Dict[str, Any]) -> Dict[str, Any]:
        context = super().get_context(name, value, attrs)
        final_attrs = context["widget"]["attrs"]
        id_ = final_attrs.get("id")

        subwidgets = []
        for index, item in enumerate(context["widget"]["value"]):
            widget_attrs = final_attrs.copy()
            if id_:
                widget_attrs["id"] = f"{id_}_array-index-{index}"

            self.subwidget.is_required = self.is_required
            subwidgets.append(self.subwidget.get_context(name, item, widget_attrs)["widget"])

        context["widget"]["subwidgets"] = subwidgets
        return context

    def value_from_datadict(self, data: QueryDict, files: MultiValueDict, name: str) -> List[Any]:
        try:
            getter = data.getlist
        except AttributeError:  # pragma: no cover
            return data.get(name)

        ret = []
        if name in data:
            ret = [value for value in getter(name) if value]
        else:
            for key in data:
                if name not in key:
                    continue

                nested_key = key.replace(f"{name}_", "", 1)

                for i, value in enumerate(getter(key)):
                    if i >= len(ret):
                        ret.append({})

                    ret[i][nested_key] = value

        return ret

    def value_omitted_from_data(self, data: QueryDict, files: MultiValueDict, name: str) -> bool:
        return False

    def format_value(self, value: Optional[List[Any]]) -> Any:
        default = self.default() if callable(self.default) else self.default
        return value or [default]


class NestedFormWidget(forms.MultiWidget):

    template_name = "subforms/nested.html"

    class Media:
        js = ["js/subforms.js"]
        css = {"all": ["css/subforms.css"]}

    def __init__(self, form_class: Type[forms.Form], attrs: Optional[Dict[str, Any]] = None):
        self.subform = form_class()
        widgets = {name: bound_field.widget for name, bound_field in self.subform.fields.items()}
        super().__init__(widgets=widgets, attrs=attrs)

    def decompress(self, value: Any) -> List[Any]:
        if isinstance(value, Mapping):
            return [value.get(name) for name in self.subform.fields.keys()]
        return [None for _ in self.subform.fields]
