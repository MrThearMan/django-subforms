from __future__ import annotations

from django import forms
from django.http import QueryDict

from subforms.fields import DynamicArrayField, NestedFormField
from subforms.widgets import DynamicArrayWidget, NestedFormWidget


class FizzBuzzForm(forms.Form):
    fizz = forms.CharField()
    buzz = forms.IntegerField()


def test_array_field__base_field():
    field = DynamicArrayField(base_field=forms.IntegerField())

    assert isinstance(field.subfield, forms.IntegerField)
    assert field.clean(["1", "2"]) == [1, 2]


def test_array_field__keep_empty_items():
    field = DynamicArrayField(remove_empty_items=False, required=False)

    assert field.clean(["1", "", "2"]) == ["1", "", "2"]


def test_array_field__has_changed__both_empty():
    field = DynamicArrayField()

    assert field.has_changed(initial=[], data=[]) is False


def test_array_field__has_changed():
    field = DynamicArrayField()

    assert field.has_changed(initial=["1"], data=["2"]) is True
    assert field.has_changed(initial=["1"], data=["1"]) is False


def test_array_field__prepare_value__list():
    field = DynamicArrayField()

    assert field.prepare_value(["1", "2"]) == ["1", "2"]


def test_array_field__prepare_value__empty_postgres_array():
    field = DynamicArrayField()

    assert field.prepare_value("{}") == []


def test_array_field__prepare_value__postgres_array():
    field = DynamicArrayField()

    assert field.prepare_value("{foo}") == ["foo"]


def test_array_field__prepare_value__postgres_array__multiple_items():
    field = DynamicArrayField()

    assert field.prepare_value("{foo,bar,baz}") == ["foo", "bar", "baz"]


def test_array_field__prepare_value__postgres_array__quoted_items():
    field = DynamicArrayField()

    value = r'{"foo, bar","say \"hi\"","back\\slash","{}"}'

    assert field.prepare_value(value) == ["foo, bar", 'say "hi"', "back\\slash", "{}"]


def test_array_field__prepare_value__postgres_array__null():
    field = DynamicArrayField()

    assert field.prepare_value('{NULL,"NULL",null}') == [None, "NULL", None]


def test_array_field__prepare_value__postgres_array__empty_strings():
    field = DynamicArrayField()

    assert field.prepare_value('{"",""}') == ["", ""]


def test_array_field__prepare_value__postgres_array__nested():
    field = DynamicArrayField(DynamicArrayField())

    value = r'{{foo,bar},{"baz, }","say \"hi\""}}'

    assert field.prepare_value(value) == [["foo", "bar"], ["baz, }", 'say "hi"']]


def test_nested_field__prepare_value__dict():
    field = NestedFormField(FizzBuzzForm)

    assert field.prepare_value({"fizz": "1", "buzz": 2}) == {"fizz": "1", "buzz": 2}


def test_nested_field__prepare_value__hstore():
    field = NestedFormField(FizzBuzzForm)

    assert field.prepare_value('"fizz"=>"1", "buzz"=>"2"') == {"fizz": "1", "buzz": "2"}


def test_array_widget__value_from_datadict__key_without_index():
    widget = DynamicArrayWidget()

    data = QueryDict(mutable=True)
    data["bar__0"] = "1"
    data["bar__foo"] = "2"

    assert widget.value_from_datadict(data=data, files=QueryDict(), name="bar") == ["1"]


def test_array_widget__get_context__no_id():
    widget = DynamicArrayWidget()

    context = widget.get_context(name="bar", value=["1"], attrs=None)

    subwidgets = context["widget"]["subwidgets"]
    assert len(subwidgets) == 1
    assert subwidgets[0]["name"] == "bar__0"
    assert "id" not in subwidgets[0]["attrs"]


def test_nested_widget__get_context__no_id():
    widget = NestedFormWidget(form_class=FizzBuzzForm)

    context = widget.get_context(name="bar", value={"fizz": "1"}, attrs=None)

    subwidgets = context["widget"]["subwidgets"]
    assert [subwidget["name"] for subwidget in subwidgets] == ["bar__fizz", "bar__buzz"]
    assert all("id" not in subwidget["attrs"] for subwidget in subwidgets)
