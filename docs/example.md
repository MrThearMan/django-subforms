# Example

Given the following model:

```python
from django.db import models

class Thing(models.Model):
    nested = models.JSONField(default=dict)
    array = models.JSONField(default=list)
    dict = models.JSONField(default=dict)
    required = models.JSONField()
```

We can create the following ModelAdmin

```python
from django.contrib import admin
from .models import Thing

@admin.register(Thing)
class AdminThing(admin.ModelAdmin):
    pass
```

We can add a custom form to it using the nested form to it using
`NestedFormField` and `DynamicArrayField`.

```python
from django import forms
from subforms.fields import DynamicArrayField, NestedFormField
from .models import Thing

class FizzBuzzForm(forms.Form):
    fizz = forms.CharField()
    buzz = forms.IntegerField()


class NestedArrayForm(forms.Form):
    foo = forms.IntegerField()
    bar = DynamicArrayField(subfield=NestedFormField(subform=FizzBuzzForm))


class SubArrayForm(forms.Form):
    foo = forms.IntegerField()
    bar = DynamicArrayField(subfield=NestedFormField(subform=NestedArrayForm))


class ExampleForm(forms.Form):
    foo = forms.CharField()
    bar = NestedFormField(subform=FizzBuzzForm)


class RequiredForm(forms.Form):
    fizz = forms.CharField()
    buzz = forms.CharField()


class ThingForm(forms.ModelForm):
    nested = NestedFormField(subform=ExampleForm)
    array = DynamicArrayField(subfield=NestedFormField(subform=ExampleForm))
    dict = NestedFormField(subform=SubArrayForm)
    required = DynamicArrayField(subfield=NestedFormField(subform=RequiredForm))

    class Meta:
        model = Thing
        fields = [
            "nested",
            "array",
            "dict",
            "required",
        ]
```

This will create the following form in the admin panel:

![Example image](./img/example.png)

And the data will be saved in the following from:

```python
thing = {
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
    ],
    "dict": {
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
    "required": [
        {
            "fizz": "11",
            "buzz": "12",
        },
    ],
}
```

The nested forms will validate each of the fields, and errors
will be shown like this:

![Error image](./img/error.png)
