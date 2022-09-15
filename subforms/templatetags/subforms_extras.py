from django import template


__all__ = [
    "replace",
]


register = template.Library()


@register.filter
def replace(value: str, arg: str):
    to_replace, replace_with = arg.split("|", maxsplit=1)
    return value.replace(to_replace, replace_with)
