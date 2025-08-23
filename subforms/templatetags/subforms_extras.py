from __future__ import annotations

from django import template

__all__ = [
    "replace",
]


register = template.Library()


@register.filter
def replace(value: str, arg: str) -> str:
    to_replace, replace_with = arg.split("|", maxsplit=1)
    return value.replace(to_replace, replace_with)
