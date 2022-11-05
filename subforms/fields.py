import copy
from itertools import chain
from typing import Any, Dict, List, Optional, Type, Union

from django import forms
from django.contrib.postgres.utils import prefix_validation_error
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy

from .widgets import DynamicArrayWidget, KeyValueWidget, NestedFormWidget


__all__ = [
    "DynamicArrayField",
    "KeyValueField",
    "NestedFormField",
]


class MultiValueField(forms.Field):

    default_error_messages = {
        "too_long": gettext_lazy("Ensure there are %(max_length)s or fewer items (currently %(items)s)."),
    }

    def __init__(self, **kwargs: Any):
        self.default = kwargs.pop("default", None)
        self.max_length = kwargs.pop("max_length", None)
        super().__init__(**kwargs)

    def clean(self, value: List[Any]) -> List[Any]:
        cleaned_data: list[Any] = []
        errors: list[ValidationError] = []

        if value is not None:
            value = [x for x in value if x]
            error = self.check_max_length(value)
            if error:
                errors.append(error)

            for index, item in enumerate(value):
                data = self.clean_item(index, item)
                if isinstance(data, ValidationError):
                    errors.append(data)
                else:
                    cleaned_data.append(data)

        if not value:
            cleaned_data = self.default() if callable(self.default) else self.default

        if cleaned_data is None and self.initial is not None:  # pragma: no cover
            cleaned_data = self.initial() if callable(self.initial) else self.initial

        if errors:
            raise ValidationError(list(chain.from_iterable(errors)))

        if not cleaned_data and self.required:
            raise ValidationError(self.error_messages["required"])

        out = self.compress(cleaned_data)
        self.validate(out)
        self.run_validators(out)
        return out

    def validate(self, value: List) -> None:
        pass

    def has_changed(self, initial: Dict[str, Any], data: Dict[str, Any]) -> bool:  # pragma: no cover
        if not data and not initial:
            return False
        return super().has_changed(initial, data)

    def check_max_length(self, value: Any) -> Optional[ValidationError]:  # pragma: no cover
        raise NotImplementedError("Subclasses must implement this method.")

    def clean_item(self, index: int, item: Any) -> Any:  # pragma: no cover
        raise NotImplementedError("Subclasses must implement this method.")

    def compress(self, data_list: List) -> Any:  # pragma: no cover
        raise NotImplementedError("Subclasses must implement this method.")


class DynamicArrayField(MultiValueField):
    """From field that can wrap other form fields to expanded lists."""

    default_error_messages = {
        "item_invalid": gettext_lazy("Validation error on item %(index)s:"),
    }

    def __init__(self, subfield: Union[Type[forms.Field], forms.Field] = forms.CharField, **kwargs: Any):
        # Compatibility with 'django.contrib.postgres.fields.array.ArrayField'
        if "base_field" in kwargs:  # pragma: no cover
            subfield = kwargs.pop("base_field")

        self.subfield: forms.Field = subfield() if isinstance(subfield, type) else copy.deepcopy(subfield)
        kwargs.setdefault(
            "widget",
            self.widget(subwidget=self.subfield.widget)
            if issubclass(self.widget, DynamicArrayWidget)
            else DynamicArrayWidget(subwidget=self.subfield.widget),
        )
        super().__init__(**kwargs)

    def check_max_length(self, value: Any) -> Optional[ValidationError]:
        items = len(value)
        if self.max_length is not None and items > self.max_length:
            return ValidationError(self.error_messages["too_long"] % {"max_length": self.max_length, "items": items})
        return None

    def clean_item(self, index: int, item: Any) -> Any:
        try:
            return self.subfield.clean(item)
        except ValidationError as error:
            return prefix_validation_error(
                error,
                self.error_messages["item_invalid"],
                code="item_invalid",
                params={"index": index},
            )

    def compress(self, data_list: List) -> Any:
        return data_list


class KeyValueField(MultiValueField):
    """Form field that can be used to save any number of key value pairs."""

    default_error_messages = {
        "key_invalid": gettext_lazy("Validation error on key %(index)s:"),
        "value_invalid": gettext_lazy("Validation error on value %(index)s:"),
    }

    def __init__(self, value_field: Union[Type[forms.Field], forms.Field] = forms.CharField, **kwargs: Any):
        self.key_field = forms.CharField()
        self.value_field = value_field() if isinstance(value_field, type) else copy.deepcopy(value_field)

        kwargs.setdefault(
            "widget",
            self.widget(key_widget=value_field.widget, value_widget=value_field.widget)
            if issubclass(self.widget, KeyValueWidget)
            else KeyValueWidget(key_widget=value_field.widget, value_widget=value_field.widget),
        )
        super().__init__(**kwargs)

    def check_max_length(self, value: Any) -> Optional[ValidationError]:
        items = len(value) // 2
        if self.max_length is not None and items > self.max_length:
            return ValidationError(self.error_messages["too_long"] % {"max_length": self.max_length, "items": items})
        return None

    def clean_item(self, index: int, item: Any) -> Any:
        is_key = index % 2 == 0
        try:
            if is_key:
                return self.key_field.clean(item)
            return self.value_field.clean(item)
        except ValidationError as error:
            code = "key_invalid" if is_key else "value_invalid"
            return prefix_validation_error(
                error,
                self.error_messages[code],
                code=code,
                params={"index": index // 2},
            )

    def compress(self, data_list: List) -> Any:
        data = {}
        data_iterable = iter(data_list)
        while True:
            try:
                key = next(data_iterable)
                value = next(data_iterable)
                data[key] = value
            except StopIteration:
                break

        return data


class NestedFormField(forms.MultiValueField):
    """Form field that can wrap other forms as nested fields."""

    def __init__(self, subform: Union[Type[forms.Form], forms.Form], **kwargs: Any):
        self.subform: forms.Form = subform() if isinstance(subform, type) else copy.deepcopy(subform)
        kwargs.setdefault("require_all_fields", False)
        kwargs.setdefault(
            "widget",
            self.widget(form_class=subform)
            if issubclass(self.widget, NestedFormWidget)
            else NestedFormWidget(form_class=subform),
        )
        super().__init__(
            tuple(self.subform.fields.values()),
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

    def compress(self, data_list: List) -> Dict[str, Any]:
        return {key: data_list[i] for i, key in enumerate(self.subform.fields.keys())}
