import pytest
from bs4 import BeautifulSoup
from django import forms
from django.http import HttpResponse, QueryDict

from subforms.fields import DynamicArrayField
from tests.myapp.admin import ThingForm
from tests.myapp.models import Thing


pytestmark = pytest.mark.django_db


def test_admin_form_add(django_client):
    result: HttpResponse = django_client.get("/admin/myapp/thing/add/", follow=True)
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

    add_button = array_value.find(name="a", attrs={"class": "add-array-item"})
    assert add_button is not None
    assert add_button.text == "Add item"

    remove_button = array_value.find(name="a", attrs={"class": "remove-array-item"})
    assert remove_button is not None

    items = array_value.findAll(name="li", attrs={"class": "dynamic-array-item"})
    assert len(items) == 1

    array_nested = items[0].find(name="div", attrs={"class": "nested-form"})
    assert array_nested is not None

    array_foo = array_nested.find(name="input", attrs={"name": "array_foo"})
    assert array_foo is not None

    array_bar = array_nested.find(name="div", attrs={"class": "nested-form"})
    assert array_foo is not None

    array_bar_fizz = array_bar.find(name="input", attrs={"name": "array_bar_fizz"})
    assert array_bar_fizz is not None

    array_bar_fuzz = array_bar.find(name="input", attrs={"name": "array_bar_buzz"})
    assert array_bar_fuzz is not None


def test_admin_form__edit(django_client):

    thing = Thing.objects.create(
        nested={"foo": "1", "bar": {"fizz": "2", "buzz": 3}},
        array=[{"foo": "4", "bar": {"fizz": "5", "buzz": 6}}, {"foo": "7", "bar": {"fizz": "8", "buzz": 9}}],
    )

    result: HttpResponse = django_client.get(f"/admin/myapp/thing/{thing.id}/change", follow=True)
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

    add_button = array_value.find(name="a", attrs={"class": "add-array-item"})
    assert add_button is not None
    assert add_button.text == "Add item"

    remove_button = array_value.find(name="a", attrs={"class": "remove-array-item"})
    assert remove_button is not None

    items = array_value.findAll(name="li", attrs={"class": "dynamic-array-item"})
    assert len(items) == 2

    array_nested_1 = items[0].find(name="div", attrs={"class": "nested-form"})
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

    array_nested_2 = items[1].find(name="div", attrs={"class": "nested-form"})
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


def test_form():

    data = {
        "nested_foo": ["1"],
        "nested_bar_fizz": ["2"],
        "nested_bar_buzz": [3],
        "array_foo": ["4", "7"],
        "array_bar_fizz": ["5", "8"],
        "array_bar_buzz": [6, 9],
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
    }


def test_form__missing__nested_bar_buzz():

    data = {
        "nested_foo": ["1"],
        "nested_bar_fizz": ["2"],
        "nested_bar_buzz": [],
        "array_foo": ["4", "7"],
        "array_bar_fizz": ["5", "8"],
        "array_bar_buzz": [6, 9],
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
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)
    assert form.is_bound
    assert form.errors == {"array": ["Validation error on item 0: Bar:  Fizz: This field is required."]}


def test_form__array_of_char():
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


def test_form__array_of_char__max_length():
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
    assert form.errors == {"bar": ["Ensure there are 1 or fewer items in this list (currently 2)."]}
