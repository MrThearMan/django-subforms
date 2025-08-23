from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

import pytest
from bs4 import BeautifulSoup
from django import forms
from django.contrib.admin.helpers import AdminForm
from django.http import HttpResponse, QueryDict

from example_project.app.admin import ThingForm
from example_project.app.models import Thing
from subforms.fields import DynamicArrayField, NestedFormField

if TYPE_CHECKING:
    from bs4 import Tag
    from django.forms import BoundField
    from django.http import HttpResponse


pytestmark = [
    pytest.mark.django_db,
]


@dataclasses.dataclass
class FizzBuzzForm:
    fizz: Tag
    buzz: Tag


@dataclasses.dataclass
class NestedField:
    foo: Tag
    bar: FizzBuzzForm


@dataclasses.dataclass
class ArrayField:
    foo: Tag
    bar: FizzBuzzForm


@dataclasses.dataclass
class NestedDictField:
    foo: Tag
    bar: list[FizzBuzzForm]


@dataclasses.dataclass
class DictField:
    foo: Tag
    bar: list[NestedDictField]


@dataclasses.dataclass
class RequiredField:
    fizz: Tag
    buzz: Tag


def get_nested_field(form: BeautifulSoup) -> NestedField:
    nested: Tag = form.find(name="div", attrs={"class": "field-nested"})
    assert nested is not None

    foo: Tag = nested.find(name="input", attrs={"name": "nested__foo"})
    assert foo is not None

    bar__fizz: Tag = nested.find(name="input", attrs={"name": "nested__bar__fizz"})
    assert bar__fizz is not None

    bar__buzz: Tag = nested.find(name="input", attrs={"name": "nested__bar__buzz"})
    assert bar__buzz is not None

    return NestedField(
        foo=foo,
        bar=FizzBuzzForm(
            fizz=bar__fizz,
            buzz=bar__buzz,
        ),
    )


def get_array_field(form: BeautifulSoup) -> list[ArrayField]:
    array = form.find(name="div", attrs={"class": "field-array"})
    assert array is not None

    array_foo = array.find(name="input", attrs={"name": "array__0__foo"})
    assert array_foo is not None

    array_bar_fizz = array.find(name="input", attrs={"name": "array__0__bar__fizz"})
    assert array_bar_fizz is not None

    array_bar_fuzz = array.find(name="input", attrs={"name": "array__0__bar__buzz"})
    assert array_bar_fuzz is not None

    return [
        ArrayField(
            foo=array_foo,
            bar=FizzBuzzForm(
                fizz=array_bar_fizz,
                buzz=array_bar_fuzz,
            ),
        ),
    ]


def get_dict_field(form: BeautifulSoup) -> DictField:
    dict_field = form.find(name="div", attrs={"class": "field-dict"})
    assert dict_field is not None

    dict_foo = dict_field.find(name="input", attrs={"name": "dict__foo"})
    assert dict_foo is not None

    dict_bar_foo = dict_field.find(name="input", attrs={"name": "dict__bar__0__foo"})
    assert dict_bar_foo is not None

    dict__bar__bar__fizz = dict_field.find(name="input", attrs={"name": "dict__bar__0__bar__0__fizz"})
    assert dict__bar__bar__fizz is not None

    dict__bar__bar__buzz = dict_field.find(name="input", attrs={"name": "dict__bar__0__bar__0__buzz"})
    assert dict__bar__bar__buzz is not None

    return DictField(
        foo=dict_foo,
        bar=[
            NestedDictField(
                foo=dict_bar_foo,
                bar=[
                    FizzBuzzForm(
                        fizz=dict__bar__bar__fizz,
                        buzz=dict__bar__bar__buzz,
                    ),
                ],
            ),
        ],
    )


def get_required_field(form: BeautifulSoup) -> list[RequiredField]:
    required_field = form.find(name="div", attrs={"class": "field-required"})
    assert required_field is not None

    required_fizz = required_field.find(name="input", attrs={"name": "required__0__fizz"})
    assert required_fizz is not None

    required_buzz = required_field.find(name="input", attrs={"name": "required__0__buzz"})
    assert required_buzz is not None

    return [
        RequiredField(
            fizz=required_fizz,
            buzz=required_buzz,
        ),
    ]


def test_admin_form_add(django_client):
    result: HttpResponse = django_client.get("/admin/app/thing/add/", follow=True)  # type: ignore[assignment]

    assert result.status_code == 200, result.content

    soup = BeautifulSoup(result.content, features="html.parser")
    form = soup.find(name="form", attrs={"id": "thing_form"})
    assert form is not None

    # Check that all fields are present
    get_nested_field(form)
    get_array_field(form)
    get_dict_field(form)
    get_required_field(form)


def test_admin_form__edit(django_client):
    thing = Thing.objects.create(
        nested={
            "foo": "1",
            "bar": {
                "fizz": "2",
                "buzz": 3,
            },
        },
        array=[
            {
                "foo": "4",
                "bar": {
                    "fizz": "5",
                    "buzz": 6,
                },
            },
        ],
        dict={
            "foo": 7,
            "bar": [
                {
                    "foo": 8,
                    "bar": [
                        {
                            "fizz": "9",
                            "buzz": 10,
                        },
                    ],
                },
            ],
        },
        required=[
            {
                "fizz": "11",
                "buzz": "12",
            },
        ],
    )

    result: HttpResponse = django_client.get(f"/admin/app/thing/{thing.id}/change", follow=True)  # type: ignore[assignment]

    assert result.status_code == 200, result.content

    soup = BeautifulSoup(result.content, features="html.parser")
    form = soup.find(name="form", attrs={"id": "thing_form"})
    assert form is not None

    nested_field = get_nested_field(form)

    assert nested_field.foo.get("value") == "1"
    assert nested_field.bar.fizz.get("value") == "2"
    assert nested_field.bar.buzz.get("value") == "3"

    array_field = get_array_field(form)

    assert array_field[0].foo.get("value") == "4"
    assert array_field[0].bar.fizz.get("value") == "5"
    assert array_field[0].bar.buzz.get("value") == "6"

    dict_field = get_dict_field(form)

    assert dict_field.foo.get("value") == "7"
    assert dict_field.bar[0].foo.get("value") == "8"
    assert dict_field.bar[0].bar[0].fizz.get("value") == "9"
    assert dict_field.bar[0].bar[0].buzz.get("value") == "10"

    required_field = get_required_field(form)

    assert required_field[0].fizz.get("value") == "11"
    assert required_field[0].buzz.get("value") == "12"


def test_form():
    data = {
        #
        # nested
        "nested__foo": ["1"],
        "nested__bar__fizz": ["2"],
        "nested__bar__buzz": ["3"],
        #
        # array
        "array__0__foo": ["4"],
        "array__0__bar__fizz": ["5"],
        "array__0__bar__buzz": ["6"],
        #
        # dict
        "dict__foo": ["7"],
        "dict__bar__0__foo": ["8"],
        "dict__bar__0__bar__0__fizz": ["9"],
        "dict__bar__0__bar__0__buzz": ["10"],
        #
        # required
        "required__0__fizz": ["11"],
        "required__0__buzz": ["12"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)
    assert form.is_valid(), form.errors

    cleaned_data = form.cleaned_data

    assert cleaned_data == {
        "nested": {"foo": "1", "bar": {"buzz": 3, "fizz": "2"}},
        "array": [{"foo": "4", "bar": {"buzz": 6, "fizz": "5"}}],
        "dict": {"foo": 7, "bar": [{"foo": 8, "bar": [{"buzz": 10, "fizz": "9"}]}]},
        "required": [{"buzz": "12!", "fizz": "11!"}],
    }


def test_form__missing__all():
    form_data = QueryDict(mutable=True)

    form = ThingForm(data=form_data)

    assert form.errors == {
        "array": ["This field is required."],
        "nested": [
            "foo: This field is required.",
            "bar: fizz: This field is required.",
            "bar: buzz: This field is required.",
        ],
        "dict": [
            "foo: This field is required.",
            "bar: This field is required.",
        ],
        "required": ["This field is required."],
    }


def test_form__missing__nested_bar_buzz():
    data = {
        #
        # nested
        "nested__foo": ["1"],
        "nested__bar__fizz": ["2"],
        "nested__bar__buzz": [],
        #
        # array
        "array__0__foo": ["4"],
        "array__0__bar__fizz": ["5"],
        "array__0__bar__buzz": ["6"],
        #
        # dict
        "dict__foo": ["7"],
        "dict__bar__0__foo": ["8"],
        "dict__bar__0__bar__0__fizz": ["9"],
        "dict__bar__0__bar__0__buzz": ["10"],
        #
        # required
        "required__0__fizz": ["11"],
        "required__0__buzz": ["12"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)

    assert form.errors == {"nested": ["bar: buzz: This field is required."]}


def test_form__missing__array_bar_fizz_1():
    data = {
        #
        # nested
        "nested__foo": ["1"],
        "nested__bar__fizz": ["2"],
        "nested__bar__buzz": ["3"],
        #
        # array
        "array__0__foo": ["4"],
        "array__0__bar__fizz": [],
        "array__0__bar__buzz": ["6"],
        #
        # dict
        "dict__foo": ["7"],
        "dict__bar__0__foo": ["8"],
        "dict__bar__0__bar__0__fizz": ["9"],
        "dict__bar__0__bar__0__buzz": ["10"],
        #
        # required
        "required__0__fizz": ["11"],
        "required__0__buzz": ["12"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)

    assert form.errors == {"array": ["index 0: bar: fizz: This field is required."]}


def test_form__missing__required():
    data = {
        #
        # nested
        "nested__foo": ["1"],
        "nested__bar__fizz": ["2"],
        "nested__bar__buzz": ["3"],
        #
        # array
        "array__0__foo": ["4"],
        "array__0__bar__fizz": ["5"],
        "array__0__bar__buzz": ["6"],
        #
        # dict
        "dict__foo": ["7"],
        "dict__bar__0__foo": ["8"],
        "dict__bar__0__bar__0__fizz": ["9"],
        "dict__bar__0__bar__0__buzz": ["10"],
        #
        # required
        "required__0__fizz": [],
        "required__0__buzz": [],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)

    assert form.errors == {
        "required": [
            "index 0: fizz: This field is required.",
            "index 0: buzz: This field is required.",
        ],
    }


def test_form__missing__required__raise_error():
    data = {
        #
        # nested
        "nested__foo": ["1"],
        "nested__bar__fizz": ["2"],
        "nested__bar__buzz": ["3"],
        #
        # array
        "array__0__foo": ["4"],
        "array__0__bar__fizz": ["5"],
        "array__0__bar__buzz": ["6"],
        #
        # dict
        "dict__foo": ["7"],
        "dict__bar__0__foo": ["8"],
        "dict__bar__0__bar__0__fizz": ["9"],
        "dict__bar__0__bar__0__buzz": ["10"],
        #
        # required
        "required__0__fizz": ["raise"],
        "required__0__buzz": ["12"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)

    assert form.errors == {"required": ["index 0: fizz: This value is not allowed"]}


def test_form__missing__required__raise_error__non_field_error():
    data = {
        #
        # nested
        "nested__foo": ["1"],
        "nested__bar__fizz": ["2"],
        "nested__bar__buzz": ["3"],
        #
        # array
        "array__0__foo": ["4"],
        "array__0__bar__fizz": ["5"],
        "array__0__bar__buzz": ["6"],
        #
        # dict
        "dict__foo": ["7"],
        "dict__bar__0__foo": ["8"],
        "dict__bar__0__bar__0__fizz": ["9"],
        "dict__bar__0__bar__0__buzz": ["10"],
        #
        # required
        "required__0__fizz": ["error"],
        "required__0__buzz": ["12"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)

    assert form.errors == {"required": ["index 0: This value is not allowed"]}


def test_form__array():
    class ExampleForm(forms.Form):
        foo = forms.CharField()
        bar = DynamicArrayField()

    data = {
        "foo": ["1"],
        "bar__0": ["2"],
        "bar__1": ["3"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ExampleForm(data=form_data)
    assert form.is_valid(), form.errors

    assert form.cleaned_data == {
        "foo": "1",
        "bar": ["2", "3"],
    }


def test_form__array__max_length():
    class ExampleForm(forms.Form):
        foo = forms.CharField()
        bar = DynamicArrayField(max_length=1)

    data = {
        "foo": ["1"],
        "bar__0": ["2"],
        "bar__1": ["3"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ExampleForm(data=form_data)

    assert not form.is_valid()
    assert form.errors == {"bar": ["Ensure there are 1 or fewer items (currently 2)."]}


def test_form__array_nested():
    class FizzBuzzForm(forms.Form):
        fizz = forms.CharField()
        buzz = forms.IntegerField()

    class SubForm(forms.Form):
        foo = forms.IntegerField()
        bar = DynamicArrayField(NestedFormField(FizzBuzzForm))

    class ExampleForm(forms.Form):
        foo = forms.IntegerField()
        array = DynamicArrayField(NestedFormField(SubForm))

    data = {
        "foo": ["0"],
        "array__0__foo": ["1"],
        "array__0__bar__0__fizz": ["2"],
        "array__0__bar__0__buzz": ["3"],
        "array__0__bar__1__fizz": ["4"],
        "array__0__bar__1__buzz": ["5"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ExampleForm(data=form_data)
    assert form.is_valid(), form.errors

    assert form.cleaned_data == {
        "foo": 0,
        "array": [
            {
                "foo": 1,
                "bar": [
                    {"fizz": "2", "buzz": 3},
                    {"fizz": "4", "buzz": 5},
                ],
            },
        ],
    }


def test_admin_form():
    data = {
        #
        # nested
        "nested__foo": ["1"],
        "nested__bar__fizz": ["2"],
        "nested__bar__buzz": ["3"],
        #
        # array
        "array__0__foo": ["4"],
        "array__0__bar__fizz": ["5"],
        "array__0__bar__buzz": ["6"],
        #
        # dict
        "dict__foo": ["7"],
        "dict__bar__0__foo": ["8"],
        "dict__bar__0__bar__0__fizz": ["9"],
        "dict__bar__0__bar__0__buzz": ["10"],
        #
        # required
        "required__0__fizz": ["11"],
        "required__0__buzz": ["12"],
    }

    form_data = QueryDict(mutable=True)
    for key, value in data.items():
        form_data.setlist(key, value)

    form = ThingForm(data=form_data)
    assert form.is_valid(), form.errors

    fieldsets = [(None, {"fields": ["nested", "array", "dict", "required"]})]

    admin_form = AdminForm(
        form=form,
        fieldsets=fieldsets,
        prepopulated_fields={},
        readonly_fields=(),
        model_admin=None,
    )

    values: dict[str, Any] = {}

    for fieldset in admin_form:
        for field_line in fieldset:
            for admin_field in field_line:
                bound_field: BoundField = admin_field.field
                values[bound_field.name] = bound_field.value()

    assert values == {
        "nested": {"foo": "1", "bar": {"buzz": "3", "fizz": "2"}},
        "array": [{"foo": "4", "bar": {"buzz": "6", "fizz": "5"}}],
        "dict": {"foo": "7", "bar": [{"foo": "8", "bar": [{"buzz": "10", "fizz": "9"}]}]},
        "required": [{"buzz": "12", "fizz": "11"}],
    }
