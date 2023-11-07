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


class RequiredForm(forms.Form):
    fizz = forms.CharField()
    buzz = forms.CharField()

    def clean(self):
        for field, value in self.cleaned_data.items():
            if value == "raise":
                msg = "This value is not allowed"
                raise forms.ValidationError({field: msg})
            if value == "error":
                msg = "This value is not allowed"
                raise forms.ValidationError(msg)
            self.cleaned_data[field] = f"{value}!"


class ThingForm(forms.ModelForm):
    nested = NestedFormField(subform=ExampleForm)
    array = DynamicArrayField(subfield=NestedFormField(subform=ExampleForm))
    dict = KeyValueField()
    required = DynamicArrayField(subfield=NestedFormField(subform=RequiredForm))

    class Meta:
        model = Thing
        fields = [
            "nested",
            "array",
            "dict",
            "required",
        ]


@admin.register(Thing)
class AdminThing(admin.ModelAdmin):
    form = ThingForm
