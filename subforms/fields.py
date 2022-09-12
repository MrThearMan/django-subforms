import copy
from itertools import chain
from typing import Any, Dict, List, Type, Union

from django import forms
from django.contrib.postgres.utils import prefix_validation_error
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy

from .widgets import DynamicArrayWidget, NestedFormWidget


__all__ = [
    "DynamicArrayField",
    "NestedFormField",
]


class DynamicArrayField(forms.Field):
    """From field that can wrap other form fields to expanded lists."""

    default_error_messages = {
        "item_invalid": gettext_lazy("Validation error on item %(index)s:"),
    }

    def __init__(
        self,
        subfield: Union[Type[forms.Field], forms.Field] = forms.CharField,
        **kwargs,
    ):
        self.subfield: forms.Field = subfield() if isinstance(subfield, type) else copy.deepcopy(subfield)
        self.default = kwargs.pop("default", None)
        kwargs.setdefault("widget", DynamicArrayWidget(subwidget=self.subfield.widget))
        super().__init__(**kwargs)

    def clean(self, value: List[Any]) -> List[Any]:
        cleaned_data: list[Any] = []
        errors: list[ValidationError] = []

        if value is not None:
            value = [x for x in value if x]

            for index, item in enumerate(value):
                try:
                    cleaned_data.append(self.subfield.clean(item))
                except ValidationError as error:
                    errors.append(
                        prefix_validation_error(
                            error,
                            self.error_messages["item_invalid"],
                            code="item_invalid",
                            params={"index": index},
                        )
                    )

        if not value:
            cleaned_data = self.default() if callable(self.default) else self.default

        if cleaned_data is None and self.initial is not None:  # pragma: no cover
            cleaned_data = self.initial() if callable(self.initial) else self.initial

        if errors:
            raise ValidationError(list(chain.from_iterable(errors)))

        if not cleaned_data and self.required:
            raise ValidationError(self.error_messages["required"])

        return cleaned_data

    def has_changed(self, initial: Dict[str, Any], data: Dict[str, Any]) -> bool:  # pragma: no cover
        if not data and not initial:
            return False
        return super().has_changed(initial, data)


class NestedFormField(forms.MultiValueField):
    """Form field that can wrap other forms as nested fields."""

    def __init__(self, subform: Union[Type[forms.Form], forms.Form], **kwargs):
        self.subform: forms.Form = subform() if isinstance(subform, type) else copy.deepcopy(subform)
        kwargs.setdefault("require_all_fields", False)
        super().__init__(
            fields=tuple(self.subform.fields.values()),
            widget=NestedFormWidget(form_class=subform),
            **kwargs,
        )

    def clean(self, value: any) -> Dict[str, Any]:
        clean_data = []
        errors = []

        for i, (name, field) in enumerate(self.subform.fields.items()):

            try:
                # Regular field
                field_value = value[name]

            # Nested form field
            except TypeError:
                field_value = value[i]

            # Nested array field
            except KeyError:
                field_value = {}
                for key in value:
                    if name not in key:
                        continue

                    nested_key = key.replace(f"{name}_", "", 1)
                    field_value[nested_key] = value[key]

            if field_value in self.empty_values:
                if self.require_all_fields:  # pragma: no cover
                    if self.required:
                        raise ValidationError(self.error_messages["required"], code="required")
                elif field.required:
                    errors.append(f"{name.capitalize()}: {field.error_messages['required']}")
                    continue

            try:
                clean_data.append(field.clean(field_value))
            except ValidationError as error:
                errors.append(
                    prefix_validation_error(
                        error,
                        f"{name.capitalize()}: ",
                        code=f"{name}_error",
                        params={},
                    ),
                )

        if errors:
            raise ValidationError(errors)

        out = self.compress(clean_data)
        self.validate(out)
        self.run_validators(out)
        return out

    def compress(self, data_list) -> Dict[str, Any]:
        return {key: data_list[i] for i, key in enumerate(self.subform.fields.keys())}
