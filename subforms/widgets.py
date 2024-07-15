from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Mapping

from django import forms

if TYPE_CHECKING:
    from django.http import QueryDict
    from django.utils.datastructures import MultiValueDict

__all__ = [
    "DynamicArrayWidget",
    "KeyValueWidget",
    "NestedFormWidget",
]


class MultiValueInput(forms.TextInput):
    default: Any

    def get_context(self, name: str, value: list[Any] | None, attrs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)
        attrs = context["widget"]["attrs"]
        id_ = attrs.get("id")
        values = context["widget"]["value"]
        context["widget"]["subwidgets"] = self.get_subwidgets(values, id_, name, attrs)
        return context

    def value_from_datadict(self, data: QueryDict, files: MultiValueDict, name: str) -> list[Any]:
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

    def format_value(self, value: list[Any] | None) -> Any:
        return value or self.default

    def get_subwidgets(self, context: Any, id_: int, name: str, attrs: dict) -> list:  # pragma: no cover
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)


class DynamicArrayWidget(MultiValueInput):
    template_name = "subforms/array.html"

    class Media:
        js = ["js/subforms.js"]
        css = {"all": ["css/subforms.css"]}

    def __init__(
        self,
        subwidget: type[forms.Widget] | forms.Widget = forms.TextInput,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        self.subwidget = subwidget() if isinstance(subwidget, type) else copy.deepcopy(subwidget)
        self.subwidget.is_required = self.is_required
        self.default = (None,)
        super().__init__(attrs=attrs)

    def get_subwidgets(self, context: Any, id_: int, name: str, attrs: dict) -> list:
        subwidgets = []

        for index, item in enumerate(context):
            widget_attrs = attrs.copy()
            if id_:
                widget_attrs["id"] = f"{id_}_array-index-{index}"
            subwidgets.append(self.subwidget.get_context(name, item, widget_attrs)["widget"])

        return subwidgets


class KeyValueWidget(MultiValueInput):
    template_name = "subforms/keyvalue.html"

    class Media:
        js = ["js/subforms.js"]
        css = {"all": ["css/subforms.css"]}

    def __init__(
        self,
        key_widget: type[forms.Widget] | forms.Widget = forms.TextInput,
        value_widget: type[forms.Widget] | forms.Widget = forms.TextInput,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        self.key_widget = key_widget() if isinstance(key_widget, type) else copy.deepcopy(key_widget)
        self.key_widget.is_required = self.is_required
        self.value_widget = value_widget() if isinstance(value_widget, type) else copy.deepcopy(value_widget)
        self.value_widget.is_required = self.is_required
        self.default = {None: None}
        super().__init__(attrs=attrs)

    def get_subwidgets(self, context: Any, id_: int, name: str, attrs: dict) -> list:
        subwidgets = []

        for index, (key, value) in enumerate(context.items()):
            widget_attrs_key = attrs.copy()
            widget_attrs_value = attrs.copy()
            if id_:
                widget_attrs_key["id"] = f"{id_}_key-index-{index}"
                widget_attrs_value["id"] = f"{id_}_value-index-{index}"

            subwidgets.append(self.key_widget.get_context(name, key, widget_attrs_key)["widget"])
            subwidgets.append(self.value_widget.get_context(name, value, widget_attrs_value)["widget"])

        return subwidgets


class NestedFormWidget(forms.MultiWidget):
    template_name = "subforms/nested.html"

    class Media:
        js = ["js/subforms.js"]
        css = {"all": ["css/subforms.css"]}

    def __init__(self, form_class: type[forms.Form], attrs: dict[str, Any] | None = None) -> None:
        self.subform = form_class()
        widgets = {name: bound_field.widget for name, bound_field in self.subform.fields.items()}
        super().__init__(widgets=widgets, attrs=attrs)

    def decompress(self, value: Any) -> list[Any]:
        if isinstance(value, Mapping):
            return [value.get(name) for name in self.subform.fields]
        return [None for _ in self.subform.fields]
