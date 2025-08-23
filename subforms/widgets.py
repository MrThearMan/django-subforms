from __future__ import annotations

import copy
import re
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from django import forms

if TYPE_CHECKING:
    from collections.abc import Mapping

    from django.utils.datastructures import MultiValueDict

__all__ = [
    "DynamicArrayWidget",
    "NestedFormWidget",
]


_INDEX_PATTERN = re.compile(r"^\d+")


class DynamicArrayWidget(forms.Widget):
    """A widget that wraps a widget into a field containing a dynamic array of that widget."""

    template_name = "subforms/array.html"

    class Media:
        js = ["js/subforms.js"]
        css = {"all": ["css/subforms.css"]}

    def __init__(
        self,
        subwidget: type[forms.Widget] | forms.Widget = forms.TextInput,
        template_name: str | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        self.subwidget = subwidget() if isinstance(subwidget, type) else copy.deepcopy(subwidget)
        self.template_name = template_name or self.template_name

        self.needs_multipart_form = self.subwidget.needs_multipart_form
        self.is_localized = self.subwidget.is_localized
        self.is_required = self.subwidget.is_required

        super().__init__(attrs=attrs)

    def __deepcopy__(self, memo: dict[int, Any]) -> Any:
        obj = super().__deepcopy__(memo)
        obj.subwidget = copy.deepcopy(self.subwidget)
        return obj

    @property
    def is_hidden(self) -> bool:
        return self.subwidget.is_hidden

    @property
    def media(self) -> forms.Media:
        media = forms.Media(media=self.Media)
        media += self.subwidget.media
        return media

    def value_from_datadict(self, data: Mapping[str, Any], files: MultiValueDict, name: str) -> list[Any]:
        """
        Parse array data from the form data.

        :param data: Data from the form.
        :param files: Files from the form.
        :param name: Name of this widget.
        """
        # In some cases, this function can be hit with already processed data.
        # If this happens, we can skip the rest of the data processing.
        if name in data:
            return data[name]

        results: dict[int, Any] = {}
        nested_forms: dict[int, dict[str, Any]] = defaultdict(dict)

        for key, value in data.items():
            if not key.startswith(f"{name}__"):
                continue

            nested_key = key.removeprefix(f"{name}__")
            match = re.match(_INDEX_PATTERN, nested_key)
            if match is None:
                continue

            index = int(match.group(0))

            if nested_key.isdigit():
                results[index] = value
                continue

            # Gather nested form data
            nested_key = nested_key.removeprefix(f"{index}__")
            nested_forms[index][nested_key] = value

        # Process nested form data
        for index, nested_form in nested_forms.items():
            results[index] = self.subwidget.value_from_datadict(data=nested_form, files=files, name="")

        return list(results.values())

    def value_omitted_from_data(self, data: Mapping[str, Any], files: MultiValueDict, name: str) -> bool:
        return False

    def id_for_label(self, id_: Any) -> str:
        return ""

    def format_value(self, value: list[Any] | None) -> list[Any]:
        return value or [None]

    def get_context(self, name: str, value: list[Any] | None, attrs: dict[str, Any] | None) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)

        sub_attrs = context["widget"]["attrs"]
        sub_value = context["widget"]["value"]

        context["widget"]["subwidgets"] = self.get_subwidgets(name, sub_value, sub_attrs)

        return context

    def get_subwidgets(self, name: str, value: Any, attrs: dict[str, Any]) -> list[dict[str, Any]]:
        subwidgets: list[dict[str, Any]] = []

        for index, item_value in enumerate(value):
            sub_attrs = copy.deepcopy(attrs)

            item_name = f"{name}__{index}"
            if "id" in sub_attrs:
                sub_attrs["id"] += f"__{index}"

            subwidget_attrs = self.subwidget.get_context(item_name, item_value, sub_attrs)
            subwidget_attrs["widget"]["label"] = index
            subwidgets.append(subwidget_attrs["widget"])

        return subwidgets


class NestedFormWidget(forms.Widget):
    """A widget that wraps a form into a field."""

    template_name = "subforms/nested.html"
    use_fieldset = True

    class Media:
        js = ["js/subforms.js"]
        css = {"all": ["css/subforms.css"]}

    def __init__(
        self,
        form_class: type[forms.Form],
        template_name: str | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        self.subform = form_class()
        self.template_name = template_name or self.template_name
        self.widget_map: dict[str, forms.Widget] = {
            name: (bound_field.widget() if isinstance(bound_field.widget, type) else bound_field.widget)
            for name, bound_field in self.subform.fields.items()
        }

        self.needs_multipart_form = any(widget.needs_multipart_form for widget in self.widget_map.values())
        self.is_localized = any(widget.is_localized for widget in self.widget_map.values())
        self.is_required = any(widget.is_required for widget in self.widget_map.values())

        super().__init__(attrs=attrs)

    def __deepcopy__(self, memo: dict[int, Any]) -> Any:
        obj = super().__deepcopy__(memo)
        obj.subform = copy.deepcopy(self.subform)
        obj.widget_map = copy.deepcopy(self.widget_map)
        return obj

    @property
    def is_hidden(self) -> bool:
        return all(widget.is_hidden for widget in self.widget_map.values())

    @property
    def media(self) -> forms.Media:
        media = forms.Media(media=self.Media)
        for widget in self.widget_map.values():
            media += widget.media
        return media

    def value_from_datadict(self, data: Mapping[str, Any], files: MultiValueDict, name: Any) -> dict[str, Any]:
        """
        Parse nested form data from the form data.

        :param data: Data from the form.
        :param files: Files from the form.
        :param name: Name of this widget.
        """
        # In some cases, this function can be hit with already processed data.
        # If this happens, we can skip the rest of the data processing.
        if name in data:
            return data[name]

        results: dict[str, Any] = {}

        for widget_name, widget in self.widget_map.items():
            key = f"{name}__{widget_name}" if name else widget_name
            results[widget_name] = widget.value_from_datadict(data=data, files=files, name=key)

        return results

    def value_omitted_from_data(self, data: Mapping[str, Any], files: MultiValueDict, name: Any) -> bool:
        return all(
            widget.value_omitted_from_data(data=data, files=files, name=f"{name}__{widget_name}")
            for widget_name, widget in self.widget_map.items()
        )

    def id_for_label(self, id_: Any) -> str:
        return ""

    def format_value(self, value: dict[str, Any] | None) -> dict[str, Any]:
        return value or {}

    def get_context(self, name: str, value: dict[str, Any] | None, attrs: dict[str, Any] | None) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)

        sub_attrs = context["widget"]["attrs"]
        sub_value = context["widget"]["value"]

        context["widget"]["subwidgets"] = self.get_subwidgets(name, sub_value, sub_attrs)
        return context

    def get_subwidgets(self, name: str, value: dict[str, Any], attrs: dict[str, Any]) -> list[dict[str, Any]]:
        subwidgets: list[dict[str, Any]] = []

        for widget_name, widget in self.widget_map.items():
            widget_attrs = copy.deepcopy(attrs)

            item_name = f"{name}__{widget_name}"
            if "id" in widget_attrs:
                widget_attrs["id"] += f"__{widget_name}"

            item = value.get(widget_name)

            subwidget_attrs = widget.get_context(item_name, item, widget_attrs)
            subwidget_attrs["widget"]["label"] = widget_name.replace("_", " ").strip().title()
            subwidgets.append(subwidget_attrs["widget"])

        return subwidgets
