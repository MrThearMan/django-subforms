from __future__ import annotations

import copy
import json
from typing import Any

from django import forms
from django.contrib.postgres.utils import prefix_validation_error
from django.core.exceptions import ValidationError
from django.forms.models import ALL_FIELDS
from django.utils.translation import gettext_lazy

from .widgets import DynamicArrayWidget, NestedFormWidget

__all__ = [
    "DynamicArrayField",
    "NestedFormField",
]


class DynamicArrayField(forms.Field):
    """From field that can wrap other form fields to expanded lists."""

    default_error_messages = {
        "too_long": gettext_lazy("Ensure there are %(max_length)s or fewer items (currently %(items)s)."),
    }

    def __init__(
        self,
        subfield: type[forms.Field] | forms.Field = forms.CharField,
        *,
        remove_empty_items: bool = True,
        **kwargs: Any,
    ) -> None:
        # Compatibility with 'django.contrib.postgres.fields.array.ArrayField'
        if "base_field" in kwargs:  # pragma: no cover
            subfield = kwargs.pop("base_field")

        self.subfield: forms.Field = (
            subfield(required=kwargs.get("required", True)) if isinstance(subfield, type) else copy.deepcopy(subfield)
        )
        kwargs.setdefault(
            "widget",
            self.widget(subwidget=self.subfield.widget)
            if issubclass(self.widget, DynamicArrayWidget)
            else DynamicArrayWidget(subwidget=self.subfield.widget),
        )
        self.remove_empty_items = remove_empty_items
        self.max_length = kwargs.pop("max_length", None)
        super().__init__(**kwargs)

    def __deepcopy__(self, memo: dict[int, Any]) -> Any:
        obj = super().__deepcopy__(memo)
        obj.subfield = copy.deepcopy(self.subfield, memo)
        return obj

    def clean(self, value: list[Any]) -> list[Any]:
        cleaned_data: list[Any] = []
        errors: list[ValidationError] = []

        if self.remove_empty_items:
            value = [item for item in value if item not in self.empty_values]

        if self.max_length is not None and len(value) > self.max_length:
            error = ValidationError(
                message=self.error_messages["too_long"],
                code="too_long",
                params={"max_length": self.max_length, "items": len(value)},
            )
            errors.append(error)

        for index, item in enumerate(value):
            try:
                item_data = self.clean_item(index, item)
            except ValidationError as error:
                errors.append(error)
            else:
                cleaned_data.append(item_data)

        if errors:
            raise ValidationError(errors)

        if not cleaned_data and self.required:
            raise ValidationError(self.error_messages["required"])

        self.validate(cleaned_data)
        self.run_validators(cleaned_data)
        return cleaned_data

    def clean_item(self, index: int, item: Any) -> Any:
        try:
            return self.subfield.clean(item)
        except ValidationError as error:
            raise prefix_validation_error(
                error=error,
                prefix=gettext_lazy("index %(index)s:"),
                code="item_invalid",
                params={"index": index},
            ) from error

    def validate(self, value: list) -> None:
        pass

    def has_changed(self, initial: dict[str, Any], data: dict[str, Any]) -> bool:  # pragma: no cover
        if not data and not initial:
            return False
        return super().has_changed(initial, data)

    def prepare_value(self, value: list[Any] | str) -> list[Any]:
        if not isinstance(value, str):
            return value

        # In certain cases, when the database is recreated while Django is running
        # (e.g. during local development), Django will fail to convert a Postgres
        # Array to a Python list. In this case, we need to convert the string ourselves,
        # so that the app can still work.
        if value == "{}":
            return []
        return [self.subfield.prepare_value(value[1:-1])]


class NestedFormField(forms.Field):
    """Form field that can wrap other forms as nested fields."""

    def __init__(self, subform: type[forms.Form], **kwargs: Any) -> None:
        self.subform: type[forms.Form] = subform
        kwargs.setdefault(
            "widget",
            self.widget(form_class=subform)
            if issubclass(self.widget, NestedFormWidget)
            else NestedFormWidget(form_class=subform),
        )
        super().__init__(**kwargs)

    def __deepcopy__(self, memo: dict[int, Any]) -> Any:
        obj = super().__deepcopy__(memo)
        obj.subform = copy.deepcopy(self.subform, memo)
        return obj

    def clean(self, value: dict[str, Any]) -> dict[str, Any]:
        form = self.subform(data=value)
        if not form.is_valid():
            errors: list[str] = [
                (f"{field_name}: {error.message}" if field_name != ALL_FIELDS else error.message)
                for field_name, error_data in form.errors.items()
                for error in error_data.as_data()
            ]
            raise ValidationError(errors)

        return form.cleaned_data

    def prepare_value(self, value: dict[str, Any] | str) -> dict[str, Any]:
        if not isinstance(value, str):
            return value

        # In certain cases, when the database is recreated while Django is running
        # (e.g. during local development), Django will fail to convert a Postgres
        # HStoreField to a Python dict. In this case, we need to convert the string ourselves,
        # so that the app can still work.
        parsed = value.replace("=>", ":").replace('\\"', '"').replace('""', '"')
        parsed = "{" + parsed + "}"
        value = json.loads(parsed)

        form = self.subform()
        for key, val in value.items():
            # Recursively convert the values to Python types if necessary.
            value[key] = form.fields[key].prepare_value(val)

        return value
