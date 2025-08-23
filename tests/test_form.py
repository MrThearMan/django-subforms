from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from bs4 import BeautifulSoup
from django import forms
from django.forms import EmailField
from django.http import QueryDict

from example_project.app.admin import ThingForm
from example_project.app.models import Thing
from subforms.fields import DynamicArrayField, KeyValueField

if TYPE_CHECKING:
    from django.http import HttpResponse


pytestmark = [
    pytest.mark.django_db,
]


def test_admin_form_add(django_client):
    result: HttpResponse = django_client.get("/admin/app/thing/add/", follow=True)

    assert result.status_code == 200, result.content

    soup = BeautifulSoup(result.content, features="html.parser")

    form = soup.find(name="form", attrs={"id": "thing_form"})
    assert form is not None

    fieldset = form.find(name="fieldset")
    assert fieldset is not None

    nested = fieldset.find(name="div", attrs={"class": "field-nested"})
    assert nested is not None

    nested_value = nested.find(name="div", attrs={"class": "nested-form"})
    assert nested_value is not None

    foo = nested_value.find(name="input", attrs={"name": "nested_foo"})
    assert foo is not None

    bar = nested_value.find(name="div", attrs={"class": "nested-form"})
    assert bar is not None

    bar_fizz = bar.find(name="input", attrs={"name": "nested_bar_fizz"})
    assert bar_fizz is not None

    bar_buzz = bar.find(name="input", attrs={"name": "nested_bar_buzz"})
    assert bar_buzz is not None

    array = fieldset.find(name="div", attrs={"class": "field-array"})
    assert array is not None

    array_value = array.find(name="div", attrs={"class": "dynamic-array"})
    assert array_value is not None

    array_add_button = array_value.find(name="a", attrs={"class": "add-array-item"})
    assert array_add_button is not None
    assert array_add_button.text == "Add item"

    array_remove_button = array_value.find(name="a", attrs={"class": "remove-array-item"})
    assert array_remove_button is not None

    array_items = array_value.findAll(name="li", attrs={"class": "dynamic-array-item"})
    assert len(array_items) == 1

    array_nested = array_items[0].find(name="div", attrs={"class": "nested-form"})
    assert array_nested is not None

    array_foo = array_nested.find(name="input", attrs={"name": "array_foo"})
    assert array_foo is not None

    array_bar = array_nested.find(name="div", attrs={"class": "nested-form"})
    assert array_foo is not None

    array_bar_fizz = array_bar.find(name="input", attrs={"name": "array_bar_fizz"})
    assert array_bar_fizz is not None

    array_bar_fuzz = array_bar.find(name="input", attrs={"name": "array_bar_buzz"})
    assert array_bar_fuzz is not None

    keyvalue = fieldset.find(name="div", attrs={"class": "field-dict"})
    assert keyvalue is not None

    kayvalue_value = keyvalue.find(name="div", attrs={"class": "key-value-field"})
    assert kayvalue_value is not None

    keyvalue_add_button = kayvalue_value.find(name="a", attrs={"class": "add-key-value-item"})
    assert keyvalue_add_button is not None
    assert keyvalue_add_button.text == "Add item"

    keyvalue_remove_button = kayvalue_value.find(name="a", attrs={"class": "remove-key-value-item"})
    assert keyvalue_remove_button is not None

    keyvalue_items = kayvalue_value.findAll(name="li", attrs={"class": "key-value-item"})
    assert len(keyvalue_items) == 1

    key_input = keyvalue_items[0].find(name="input", attrs={"id": "id_dict_key-index-0"})
    assert key_input is not None

    value_input = keyvalue_items[0].find(name="input", attrs={"id": "id_dict_value-index-0"})
    assert value_input is not None


def test_admin_form__edit(django_client):
    thing = Thing.objects.create(
        nested={"foo": "1", "bar": {"fizz": "2", "buzz": 3}},
        array=[{"foo": "4", "bar": {"fizz": "5", "buzz": 6}}, {"foo": "7", "bar": {"fizz": "8", "buzz": 9}}],
        dict={"1": "2", "3": "4", "5": "6"},
        required=[{"fizz": "11", "buzz": 11}],
    )

    result: HttpResponse = django_client.get(f"/admin/app/thing/{thing.id}/change", follow=True)

    assert result.status_code == 200, result.content

    soup = BeautifulSoup(result.content, features="html.parser")

    form = soup.find(name="form", attrs={"id": "thing_form"})
    assert form is not None

    fieldset = form.find(name="fieldset")
    assert fieldset is not None

    nested = fieldset.find(name="div", attrs={"class": "field-nested"})
    assert nested is not None

    nested_value = nested.find(name="div", attrs={"class": "nested-form"})
    assert nested_value is not None

    foo = nested_value.find(name="input", attrs={"name": "nested_foo"})
    assert foo is not None
    assert foo.get("value") == "1"

    bar = nested_value.find(name="div", attrs={"class": "nested-form"})
    assert bar is not None

    bar_fizz = bar.find(name="input", attrs={"name": "nested_bar_fizz"})
    assert bar_fizz is not None
    assert bar_fizz.get("value") == "2"

    bar_buzz = bar.find(name="input", attrs={"name": "nested_bar_buzz"})
    assert bar_buzz is not None
    assert bar_buzz.get("value") == "3"

    array = fieldset.find(name="div", attrs={"class": "field-array"})
    assert array is not None

    array_value = array.find(name="div", attrs={"class": "dynamic-array"})
    assert array_value is not None

    array_add_button = array_value.find(name="a", attrs={"class": "add-array-item"})
    assert array_add_button is not None
    assert array_add_button.text == "Add item"

    array_remove_button = array_value.find(name="a", attrs={"class": "remove-array-item"})
    assert array_remove_button is not None

    array_items = array_value.findAll(name="li", attrs={"class": "dynamic-array-item"})
    assert len(array_items) == 2

    array_nested_1 = array_items[0].find(name="div", attrs={"class": "nested-form"})
    assert array_nested_1 is not None

    array_foo_1 = array_nested_1.find(name="input", attrs={"name": "array_foo"})
    assert array_foo_1 is not None
    assert array_foo_1.get("value") == "4"

    array_bar_1 = array_nested_1.find(name="div", attrs={"class": "nested-form"})
    assert array_bar_1 is not None

    array_bar_fizz_1 = array_bar_1.find(name="input", attrs={"name": "array_bar_fizz"})
    assert array_bar_fizz_1 is not None
    assert array_bar_fizz_1.get("value") == "5"

    array_bar_fuzz_1 = array_bar_1.find(name="input", attrs={"name": "array_bar_buzz"})
    assert array_bar_fuzz_1 is not None
    assert array_bar_fuzz_1.get("value") == "6"

    array_nested_2 = array_items[1].find(name="div", attrs={"class": "nested-form"})
    assert array_nested_1 is not None

    array_foo_2 = array_nested_2.find(name="input", attrs={"name": "array_foo"})
    assert array_foo_2 is not None
    assert array_foo_2.get("value") == "7"

    array_bar_2 = array_nested_2.find(name="div", attrs={"class": "nested-form"})
    assert array_bar_2 is not None

    array_bar_fizz_2 = array_bar_2.find(name="input", attrs={"name": "array_bar_fizz"})
    assert array_bar_fizz_2 is not None
    assert array_bar_fizz_2.get("value") == "8"

    array_bar_fuzz_2 = array_bar_2.find(name="input", attrs={"name": "array_bar_buzz"})
    assert array_bar_fuzz_2 is not None
    assert array_bar_fuzz_2.get("value") == "9"

    keyvalue = fieldset.find(name="div", attrs={"class": "field-dict"})
    assert keyvalue is not None

    kayvalue_value = keyvalue.find(name="div", attrs={"class": "key-value-field"})
    assert kayvalue_value is not None

    keyvalue_add_button = kayvalue_value.find(name="a", attrs={"class": "add-key-value-item"})
    assert keyvalue_add_button is not None
    assert keyvalue_add_button.text == "Add item"

    keyvalue_remove_button = kayvalue_value.find(name="a", attrs={"class": "remove-key-value-item"})
    assert keyvalue_remove_button is not None

    keyvalue_items = kayvalue_value.findAll(name="li", attrs={"class": "key-value-item"})
    assert len(keyvalue_items) == 3

    key_input_1 = keyvalue_items[0].find(name="input", attrs={"id": "id_dict_key-index-0"})
    assert key_input_1 is not None
    assert key_input_1.get("value") == "1"

    value_input_1 = keyvalue_items[0].find(name="input", attrs={"id": "id_dict_value-index-0"})
    assert value_input_1 is not None
    assert value_input_1.get("value") == "2"

    key_input_2 = keyvalue_items[1].find(name="input", attrs={"id": "id_dict_key-index-1"})
    assert key_input_2 is not None
    assert key_input_2.get("value") == "3"

    value_input_2 = keyvalue_items[1].find(name="input", attrs={"id": "id_dict_value-index-1"})
    assert value_input_2 is not None
    assert value_input_2.get("value") == "4"

    key_input_3 = keyvalue_items[2].find(name="input", attrs={"id": "id_dict_key-index-2"})
    assert key_input_3 is not None
    assert key_input_3.get("value") == "5"

    value_input_3 = keyvalue_items[2].find(name="input", attrs={"id": "id_dict_value-index-2"})
    assert value_input_3 is not None
    assert value_input_3.get("value") == "6"


def test_form():
    data = {
        "nested_foo": ["1"],
        "nested_bar_fizz": ["2"],
        "nested_bar_buzz": [3],
        "array_foo": ["4", "7"],
        "array_bar_fizz": ["5", "8"],
        "array_bar_buzz": [6, 9],
        "dict": ["1", "2", "3", "4"],
        "required_fizz": ["woo"],
        "required_buzz": ["hoo"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)
    assert form.is_bound
    assert form.errors == {}

    cleaned_data = form.clean()

    assert cleaned_data == {
        "nested": {
            "foo": "1",
            "bar": {
                "fizz": "2",
                "buzz": 3,
            },
        },
        "array": [
            {
                "foo": "4",
                "bar": {
                    "fizz": "5",
                    "buzz": 6,
                },
            },
            {
                "foo": "7",
                "bar": {
                    "fizz": "8",
                    "buzz": 9,
                },
            },
        ],
        "dict": {
            "1": "2",
            "3": "4",
        },
        "required": [
            {
                "buzz": "hoo!",
                "fizz": "woo!",
            },
        ],
    }


def test_form__missing__all():
    form_data = QueryDict(mutable=True)

    form = ThingForm(data=form_data)
    assert form.errors == {
        "array": ["This field is required."],
        "nested": [
            "Foo: This field is required.",
            "Bar:  Fizz: This field is required.",
            "Bar:  Buzz: This field is required.",
        ],
        "dict": ["This field is required."],
        "required": ["This field is required."],
    }


def test_form__missing__nested_bar_buzz():
    data = {
        "nested_foo": ["1"],
        "nested_bar_fizz": ["2"],
        "nested_bar_buzz": [],
        "array_foo": ["4", "7"],
        "array_bar_fizz": ["5", "8"],
        "array_bar_buzz": [6, 9],
        "dict": ["1", "2", "3", "4"],
        "required_fizz": ["woo"],
        "required_buzz": ["hoo"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)
    assert form.is_bound
    assert form.errors == {"nested": ["Bar:  Buzz: This field is required."]}


def test_form__missing__array_bar_fizz_1():
    data = {
        "nested_foo": ["1"],
        "nested_bar_fizz": ["2"],
        "nested_bar_buzz": [3],
        "array_foo": ["4", "7"],
        "array_bar_fizz": ["", "5"],
        "array_bar_buzz": [6, 9],
        "dict": ["1", "2", "3", "4"],
        "required_fizz": ["woo"],
        "required_buzz": ["hoo"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)
    assert form.is_bound
    assert form.errors == {"array": ["Validation error on item 0: Bar:  Fizz: This field is required."]}


def test_form__missing__required():
    data = {
        "nested_foo": ["1"],
        "nested_bar_fizz": ["2"],
        "nested_bar_buzz": [3],
        "array_foo": ["4", "7"],
        "array_bar_fizz": ["5", "8"],
        "array_bar_buzz": [6, 9],
        "dict": ["1", "2", "3", "4"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)
    assert form.is_bound
    assert form.errors == {"required": ["This field is required."]}


def test_form__missing__required__raise_error():
    data = {
        "nested_foo": ["1"],
        "nested_bar_fizz": ["2"],
        "nested_bar_buzz": [3],
        "array_foo": ["4", "7"],
        "array_bar_fizz": ["5", "8"],
        "array_bar_buzz": [6, 9],
        "dict": ["1", "2", "3", "4"],
        "required_fizz": ["raise"],
        "required_buzz": ["hoo"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)
    assert form.is_bound
    assert form.errors == {"required": ["Validation error on item 0: Fizz: This value is not allowed"]}


def test_form__missing__required__raise_error__non_field_error():
    data = {
        "nested_foo": ["1"],
        "nested_bar_fizz": ["2"],
        "nested_bar_buzz": [3],
        "array_foo": ["4", "7"],
        "array_bar_fizz": ["5", "8"],
        "array_bar_buzz": [6, 9],
        "dict": ["1", "2", "3", "4"],
        "required_fizz": ["error"],
        "required_buzz": ["hoo"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)
    assert form.is_bound
    assert form.errors == {"required": ["Validation error on item 0: This value is not allowed"]}


def test_form__array():
    class ExampleForm(forms.Form):
        foo = forms.CharField()
        bar = DynamicArrayField()

    data = {
        "foo": ["1"],
        "bar": ["2", "3"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ExampleForm(data=form_data)
    assert form.is_bound
    assert form.errors == {}

    cleaned_data = form.clean()

    assert cleaned_data == {
        "bar": ["2", "3"],
        "foo": "1",
    }


def test_form__array__max_length():
    class ExampleForm(forms.Form):
        foo = forms.CharField()
        bar = DynamicArrayField(max_length=1)

    data = {
        "foo": ["1"],
        "bar": ["2", "3"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ExampleForm(data=form_data)
    assert form.is_bound
    assert form.errors == {"bar": ["Ensure there are 1 or fewer items (currently 2)."]}


def test_form__keyvalue__incorrect_data():
    class ExampleForm(forms.Form):
        foo = forms.CharField()
        bar = KeyValueField(value_field=EmailField)

    data = {
        "foo": ["1"],
        "bar": ["2", "3"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ExampleForm(data=form_data)
    assert form.is_bound
    assert form.errors == {"bar": ["Validation error on value 0: Enter a valid email address."]}


def test_form__keyvalue__max_length():
    class ExampleForm(forms.Form):
        foo = forms.CharField()
        bar = KeyValueField(max_length=1)

    data = {
        "foo": ["1"],
        "bar": ["2", "3", "4", "5"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ExampleForm(data=form_data)
    assert form.is_bound
    assert form.errors == {"bar": ["Ensure there are 1 or fewer items (currently 2)."]}
