from django import forms
from django.contrib import admin

from subforms.fields import DynamicArrayField, KeyValueField, NestedFormField
from tests.myapp.models import Thing


class FizzBuzzForm(forms.Form):
    fizz = forms.CharField()
    buzz = forms.IntegerField()


class ExampleForm(forms.Form):
    foo = forms.CharField()
    bar = NestedFormField(subform=FizzBuzzForm)


class ThingForm(forms.ModelForm):

    nested = NestedFormField(subform=ExampleForm)
    array = DynamicArrayField(subfield=NestedFormField(subform=ExampleForm))
    dict = KeyValueField()

    class Meta:
        model = Thing
        fields = [
            "nested",
            "array",
            "dict",
        ]


@admin.register(Thing)
class AdminThing(admin.ModelAdmin):
    form = ThingForm
